import unittest
from unittest.mock import Mock, patch

import requests
from flask_jwt_extended import create_access_token

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import BotProfile, User
from app.services.bitunix_futures_client import BitunixAPIError, BitunixFuturesClient


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test-jwt-secret-that-is-at-least-32-bytes"
    SECRET_KEY = "test-secret-that-is-at-least-32-bytes"
    ENCRYPTION_KEY = "q3pLuY0vK8Jk8_VuC3RLNnGX_Z4GiQ-iGJr5R0BskSM="
    LIVE_TRADING_API_ENABLED = False


class BitunixIntegrationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.user = User(username="bitunix-user", full_name="Bitunix User")
        self.user.set_password("strong-password")
        db.session.add(self.user)
        db.session.flush()
        db.session.add(BotProfile(user_id=self.user.id))
        db.session.commit()
        self.client = self.app.test_client()
        token = create_access_token(identity=str(self.user.id))
        self.headers = {"Authorization": f"Bearer {token}"}

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    @patch("app.services.bitunix_futures_client.requests.request")
    def test_public_candles_are_normalized_and_sorted(self, request_mock):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"code": 0, "data": [{"time": 2, "open": "2", "high": "3", "low": "1", "close": "2.5", "baseVol": "10"}, {"time": 1, "open": "1", "high": "2", "low": ".5", "close": "1.5", "baseVol": "8"}]}
        request_mock.return_value = response
        candles = BitunixFuturesClient("https://fapi.bitunix.com").get_candles("BTCUSDT", limit=2)
        self.assertEqual([candle["timestamp"] for candle in candles], [1, 2])
        self.assertEqual(candles[-1]["close"], 2.5)

    @patch("app.services.bitunix_futures_client.requests.request", side_effect=requests.ConnectionError("offline"))
    def test_api_failure_is_explicit(self, _request_mock):
        with self.assertRaises(BitunixAPIError):
            BitunixFuturesClient("https://fapi.bitunix.com").get_latest_price("BTCUSDT")

    def test_live_enable_is_server_locked_by_default(self):
        response = self.client.post("/api/live/enable", headers=self.headers, json={"accept_risk_disclaimer": True})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(BotProfile.query.filter_by(user_id=self.user.id).one().live_trading_enabled)

    def test_status_never_exposes_credentials(self):
        response = self.client.get("/api/exchange/bitunix/status", headers=self.headers)
        payload = str(response.get_json())
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("api_key", payload)
        self.assertNotIn("api_secret", payload)

    def test_profile_with_legacy_symbol_is_repaired(self):
        profile = BotProfile.query.filter_by(user_id=self.user.id).one()
        profile.symbol = "DOGEUSDT"
        db.session.commit()
        response = self.client.get("/api/bot/profile", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"]["bot_profile"]["symbol"], "BTCUSDT")
        self.assertEqual(response.get_json()["data"]["supported_symbols"], ["BTCUSDT", "ETHUSDT", "SOLUSDT"])
