import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from flask_jwt_extended import create_access_token

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import BotProfile, PaperAccount, PaperPosition, PaperTrade, Subscription, User
from app.services.market_data_service import MockMarketDataProvider
from app.services.ai_signal_service import validate_signal_with_ai
from app.services.paper_trading_engine import (
    close_paper_position,
    get_or_create_paper_account,
    open_paper_position,
    monitor_open_positions,
)
from app.services.strategy_engine import build_trade_scenarios, generate_strategy_signal


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test-jwt-secret-that-is-at-least-32-bytes"
    SECRET_KEY = "test-secret-that-is-at-least-32-bytes"
    OPENAI_API_KEY = ""
    MARKET_DATA_PROVIDER = "mock"
    PAPER_TRADING_INITIAL_BALANCE = 10000
    PAPER_TRADING_DEFAULT_LEVERAGE = 1
    PAPER_CONFIDENCE_THRESHOLD = 70
    DEVELOPMENT_MODE = False


class PaperTradingTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()

        self.user = User(username="papertrader", email="paper@example.com", full_name="Paper Trader")
        self.user.set_password("strong-password")
        db.session.add(self.user)
        db.session.flush()
        now = datetime.now(UTC)
        db.session.add(
            Subscription(
                user_id=self.user.id,
                plan_name="Starter",
                status="active",
                started_at=now,
                expires_at=now + timedelta(days=30),
            )
        )
        db.session.add(
            BotProfile(
                user_id=self.user.id,
                mode="paper",
                is_enabled=True,
                symbol="BTCUSDT",
                confidence_threshold=70,
                risk_per_trade_percent=1,
                max_daily_loss_percent=3,
            )
        )
        db.session.commit()
        self.token = create_access_token(identity=str(self.user.id))
        self.client = self.app.test_client()
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def test_mock_market_data_has_realistic_ohlcv_shape(self):
        candles = MockMarketDataProvider().get_candles("BTCUSDT", limit=250)
        self.assertEqual(len(candles), 250)
        self.assertEqual(set(candles[-1]), {"open", "high", "low", "close", "volume", "timestamp"})
        self.assertGreaterEqual(candles[-1]["high"], candles[-1]["close"])
        self.assertLessEqual(candles[-1]["low"], candles[-1]["close"])

    def test_all_supported_paper_symbols_generate_market_data(self):
        provider = MockMarketDataProvider()
        for symbol in ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "AVAXUSDT", "LINKUSDT"]:
            candles = provider.get_candles(symbol, limit=250)
            self.assertEqual(len(candles), 250)
            self.assertGreater(provider.get_latest_price(symbol), 0)

    def test_long_and_short_what_if_scenarios_are_calculated(self):
        strategy_signal = {
            "market_summary": {
                "latest_price": 100,
                "ema50": 105,
                "ema200": 95,
                "rsi14": 60,
                "atr14": 2,
                "volume": 1200,
                "average_volume": 1000,
            }
        }
        scenarios = build_trade_scenarios(strategy_signal, 10000, 1, 1, 70)
        self.assertEqual(scenarios["long"]["stop_loss"], 98)
        self.assertEqual(scenarios["long"]["take_profit"], 104)
        self.assertEqual(scenarios["short"]["stop_loss"], 102)
        self.assertEqual(scenarios["short"]["take_profit"], 96)
        self.assertAlmostEqual(scenarios["long"]["risk_usdt"], 100)
        self.assertAlmostEqual(scenarios["long"]["target_profit_usdt"], 200)
        self.assertEqual(scenarios["long"]["risk_reward_ratio"], 2)

    @patch("app.services.strategy_engine.calculate_atr", return_value=2)
    @patch("app.services.strategy_engine.calculate_rsi", return_value=45)
    @patch("app.services.strategy_engine.calculate_ema", side_effect=[105, 100])
    def test_hold_confidence_uses_nearest_direction_not_fixed_fifty(self, _ema, _rsi, _atr):
        candles = [
            {"open": 101, "high": 103, "low": 99, "close": 102, "volume": 1000, "timestamp": str(index)}
            for index in range(200)
        ]
        candles[-1]["volume"] = 1500
        signal = generate_strategy_signal("BTCUSDT", candles)
        self.assertEqual(signal["action"], "HOLD")
        self.assertNotEqual(signal["confidence_base"], 50)
        self.assertGreater(signal["directional_confidence"]["short"], signal["directional_confidence"]["long"])
        self.assertEqual(signal["directional_confidence"]["bias"], "SHORT")

    def test_ai_disabled_uses_strategy_signal(self):
        signal = {"action": "LONG", "confidence_base": 75, "market_summary": {}}
        result = validate_signal_with_ai(signal)
        self.assertEqual(result["action"], "LONG")
        self.assertEqual(result["confidence"], 75)

    def test_development_registration_bootstraps_paper_trading(self):
        self.app.config.update(
            DEVELOPMENT_MODE=True,
            DEV_USERNAME="ilyanozary",
            DEV_PASSWORD="ilyalm10",
        )
        response = self.client.post(
            "/api/auth/register",
            json={"username": "ilyanozary", "password": "ilyalm10", "full_name": "Ilya Nozary"},
        )
        self.assertEqual(response.status_code, 201)
        user_id = response.get_json()["data"]["user"]["id"]
        self.assertIsNotNone(Subscription.query.filter_by(user_id=user_id, status="active").first())
        profile = BotProfile.query.filter_by(user_id=user_id).one()
        self.assertEqual(profile.mode, "paper")
        self.assertTrue(profile.is_enabled)
        self.assertAlmostEqual(float(PaperAccount.query.filter_by(user_id=user_id).one().balance_usdt), 10000)

    def test_open_and_close_virtual_position_updates_account(self):
        account = get_or_create_paper_account(self.user.id)
        position = open_paper_position(
            user_id=self.user.id,
            symbol="BTCUSDT",
            side="LONG",
            entry_price=100000,
            stop_loss=99000,
            take_profit=102000,
            confidence=75,
            margin_usdt=100,
            leverage=1,
        )
        db.session.commit()
        self.assertAlmostEqual(float(account.balance_usdt), 9900)

        trade = close_paper_position(position, 101000, "MANUAL")
        db.session.commit()
        self.assertEqual(position.status, "closed")
        self.assertEqual(trade.status, "win")
        self.assertAlmostEqual(float(trade.pnl_usdt), 1)
        self.assertAlmostEqual(float(account.balance_usdt), 10001)
        self.assertAlmostEqual(float(account.realized_pnl), 1)

    @patch("app.services.paper_trading_engine.get_latest_price", return_value=102000)
    def test_monitor_closes_position_at_take_profit(self, _price):
        open_paper_position(
            user_id=self.user.id,
            symbol="BTCUSDT",
            side="LONG",
            entry_price=100000,
            stop_loss=99000,
            take_profit=102000,
            confidence=75,
            margin_usdt=100,
            leverage=1,
        )
        db.session.commit()
        events = monitor_open_positions(self.user.id)
        self.assertTrue(events[0]["closed"])
        trade = PaperTrade.query.one()
        self.assertEqual(trade.reason, "TAKE_PROFIT")
        self.assertGreater(float(trade.pnl_usdt), 0)

    @patch("app.services.paper_trading_engine.get_latest_price", return_value=100123.45)
    def test_tick_returns_live_price_and_account(self, _price):
        response = self.client.post("/api/paper/engine/tick", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["latest_price"], 100123.45)
        self.assertEqual(payload["mode"], "paper")
        self.assertIn("account", payload)

    def test_manual_position_api_requires_auth_and_creates_position(self):
        body = {
            "symbol": "BTCUSDT",
            "side": "LONG",
            "entry_price": 100000,
            "stop_loss": 99000,
            "take_profit": 102000,
            "margin_usdt": 100,
            "leverage": 1,
            "confidence": 75,
        }
        self.assertEqual(self.client.post("/api/paper/positions/open", json=body).status_code, 401)
        response = self.client.post("/api/paper/positions/open", json=body, headers=self.headers)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.get_json()["data"]["position"]["status"] == "open")

    @patch("app.services.paper_trading_engine.monitor_open_positions", return_value=[])
    @patch(
        "app.services.paper_trading_engine.validate_signal_with_ai",
        return_value={"action": "LONG", "confidence": 80, "ai_reason": "Signal confirmed conservatively."},
    )
    @patch(
        "app.services.paper_trading_engine.generate_strategy_signal",
        return_value={
            "action": "LONG",
            "confidence_base": 80,
            "entry_price": 100000.0,
            "stop_loss": 99000.0,
            "take_profit": 102000.0,
            "strategy_reason": "Test trend alignment.",
            "market_summary": {
                "symbol": "BTCUSDT",
                "latest_price": 100000.0,
                "ema50": 99500.0,
                "ema200": 98000.0,
                "rsi14": 60.0,
                "atr14": 1000.0,
                "volume": 1200.0,
                "average_volume": 1000.0,
            },
        },
    )
    @patch("app.services.paper_trading_engine.get_candles", return_value=[{}] * 250)
    def test_engine_run_opens_only_virtual_position(self, _candles, _strategy, _ai, _monitor):
        response = self.client.post("/api/paper/engine/run-once", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertTrue(result["position_opened"])
        self.assertEqual(result["mode"], "paper")
        self.assertIn("long", result["scenario_comparison"])
        self.assertIn("short", result["scenario_comparison"])
        self.assertEqual(PaperPosition.query.filter_by(user_id=self.user.id, status="open").count(), 1)
        self.assertEqual(PaperTrade.query.count(), 0)


if __name__ == "__main__":
    unittest.main()
