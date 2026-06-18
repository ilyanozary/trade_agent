from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, ROUND_DOWN

from flask import current_app

from app.extensions import db
from app.models import BotProfile, ExchangeApiKey, LiveOrderLog, LivePosition, LiveRiskState, LiveTrade
from app.services.ai_signal_service import validate_signal_with_ai
from app.services.bitunix_futures_client import BitunixAPIError, BitunixFuturesClient
from app.services.credential_service import decrypt_secret
from app.services.market_data_service import get_candles
from app.services.strategy_engine import generate_strategy_signal


class LiveTradingBlocked(RuntimeError):
    pass


def _credentials(user_id: int) -> ExchangeApiKey:
    connection = ExchangeApiKey.query.filter_by(user_id=user_id, exchange="bitunix", is_connected=True).first()
    if not connection:
        raise LiveTradingBlocked("A validated Bitunix connection is required")
    return connection


def _client(connection: ExchangeApiKey) -> BitunixFuturesClient:
    return BitunixFuturesClient(current_app.config["BITUNIX_FUTURES_BASE_URL"], decrypt_secret(connection.api_key_encrypted), decrypt_secret(connection.api_secret_encrypted))


def _log(user_id: int, endpoint: str, request_payload: dict, response_payload: dict, status: str) -> None:
    db.session.add(LiveOrderLog.create(user_id, endpoint, request_payload, response_payload, status))
    db.session.commit()


def _balance(account: dict) -> Decimal:
    for field in ("available", "availableBalance", "equity", "marginBalance", "balance"):
        if account.get(field) is not None:
            value = Decimal(str(account[field]))
            if value > 0:
                return value
    raise LiveTradingBlocked("Bitunix account balance could not be fetched")


def get_or_create_risk_state(user_id: int) -> LiveRiskState:
    state = LiveRiskState.query.filter_by(user_id=user_id).first()
    today = datetime.now(UTC).date()
    if state is None:
        state = LiveRiskState(user_id=user_id, trading_date=today)
        db.session.add(state)
    elif state.trading_date != today:
        state.trading_date = today
        state.daily_realized_pnl = 0
        state.starting_balance = None
        state.kill_switch_active = False
        state.last_reason = None
    return state


def run_once(user_id: int) -> dict:
    if not current_app.config.get("LIVE_TRADING_API_ENABLED"):
        raise LiveTradingBlocked("Live trading is disabled by server configuration")
    profile = BotProfile.query.filter_by(user_id=user_id).first()
    if not profile or profile.mode != "live" or not profile.live_trading_enabled or not profile.is_enabled:
        raise LiveTradingBlocked("Live bot is not explicitly enabled")
    if not profile.risk_disclaimer_accepted_at:
        raise LiveTradingBlocked("Risk disclaimer has not been accepted")
    if profile.max_leverage > 3 or profile.max_open_positions < 1 or profile.confidence_threshold < 75:
        raise LiveTradingBlocked("Live risk settings violate V1 limits")
    state = get_or_create_risk_state(user_id)
    if state.kill_switch_active:
        raise LiveTradingBlocked("Kill switch is active")
    if LivePosition.query.filter(LivePosition.user_id == user_id, LivePosition.symbol == profile.symbol, LivePosition.status.in_(["open", "submitted"])).first():
        raise LiveTradingBlocked("An open position already exists for this symbol")
    if LivePosition.query.filter(LivePosition.user_id == user_id, LivePosition.status.in_(["open", "submitted"])).count() >= profile.max_open_positions:
        raise LiveTradingBlocked("Maximum open positions reached")

    client = _client(_credentials(user_id))
    account = client.get_account()
    balance = _balance(account)
    if state.starting_balance is None:
        state.starting_balance = balance
    loss_limit = Decimal(str(state.starting_balance)) * Decimal(str(profile.max_daily_loss_percent)) / 100
    if Decimal(str(state.daily_realized_pnl)) <= -loss_limit:
        profile.live_trading_enabled = False
        state.last_reason = "Daily loss limit reached"
        db.session.commit()
        raise LiveTradingBlocked(state.last_reason)

    strategy = generate_strategy_signal(profile.symbol, get_candles(profile.symbol, "15m", 200))
    ai_signal = validate_signal_with_ai(strategy)
    if ai_signal["action"] not in {"LONG", "SHORT"} or ai_signal["confidence"] < profile.confidence_threshold:
        db.session.commit()
        return {"order_placed": False, "reason": "Signal did not pass confidence and direction gates", "strategy_signal": strategy, "ai_signal": ai_signal}
    entry = Decimal(str(strategy["entry_price"]))
    stop = Decimal(str(strategy["stop_loss"]))
    take = Decimal(str(strategy["take_profit"]))
    if stop <= 0 or take <= 0 or stop == entry or take == entry:
        raise LiveTradingBlocked("A valid stop loss and take profit are mandatory")
    risk_budget = balance * Decimal(str(profile.risk_per_trade_percent)) / 100
    quantity = (risk_budget / abs(entry - stop)).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)
    max_quantity = (balance * Decimal(str(profile.max_leverage)) / entry).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)
    quantity = min(quantity, max_quantity)
    if quantity <= 0:
        raise LiveTradingBlocked("Calculated position size is zero")

    payload = {"symbol": profile.symbol, "qty": format(quantity, "f"), "side": "BUY" if ai_signal["action"] == "LONG" else "SELL", "tradeSide": "OPEN", "orderType": "MARKET", "reduceOnly": False, "tpPrice": format(take, "f"), "tpStopType": "MARK_PRICE", "tpOrderType": "MARKET", "slPrice": format(stop, "f"), "slStopType": "MARK_PRICE", "slOrderType": "MARKET"}
    try:
        response = client.place_order(payload)
        _log(user_id, "/api/v1/futures/trade/place_order", payload, response, "accepted")
        order_id = str((response.get("data") or {}).get("orderId") or "")
        if not order_id:
            raise LiveTradingBlocked("Bitunix order response did not contain an order ID")
        detail = client.get_order_detail(order_id)
        _log(user_id, "/api/v1/futures/trade/get_order_detail", {"orderId": order_id}, detail, "verified")
    except BitunixAPIError as exc:
        _log(user_id, "bitunix-live-order", payload, {"error": str(exc)}, "error")
        raise LiveTradingBlocked("Bitunix order state is uncertain; live bot has been disabled") from exc
    detail_data = detail.get("data") or {}
    order_status = str(detail_data.get("status", "UNKNOWN")).upper()
    if order_status not in {"FILLED", "NEW", "PART_FILLED"}:
        profile.live_trading_enabled = False
        state.last_reason = f"Unknown or rejected order status: {order_status}"
        db.session.commit()
        raise LiveTradingBlocked(state.last_reason)
    position_status = "open" if order_status in {"FILLED", "PART_FILLED"} else "submitted"
    position = LivePosition(user_id=user_id, exchange_order_id=order_id, symbol=profile.symbol, side=ai_signal["action"], quantity=quantity, entry_price=Decimal(str(detail_data.get("avgPrice") or entry)), stop_loss=stop, take_profit=take, leverage=profile.max_leverage, confidence=ai_signal["confidence"], status=position_status)
    trade = LiveTrade(user_id=user_id, symbol=profile.symbol, side=ai_signal["action"], exchange_order_id=order_id, entry_price=position.entry_price, quantity=quantity, status=position_status)
    db.session.add_all([position, trade])
    db.session.commit()
    return {"order_placed": True, "order_status": order_status, "position": position.to_dict(), "strategy_signal": strategy, "ai_signal": ai_signal}


def activate_kill_switch(user_id: int) -> dict:
    profile = BotProfile.query.filter_by(user_id=user_id).first()
    state = get_or_create_risk_state(user_id)
    state.kill_switch_active = True
    state.last_reason = "User activated kill switch"
    if profile:
        profile.live_trading_enabled = False
        profile.is_enabled = False
    results = []
    try:
        client = _client(_credentials(user_id))
        for symbol in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
            try:
                response = client.cancel_all_orders(symbol)
                _log(user_id, "/api/v1/futures/trade/cancel_all_orders", {"symbol": symbol}, response, "cancellation_requested")
                results.append({"symbol": symbol, "requested": True})
            except BitunixAPIError as exc:
                _log(user_id, "/api/v1/futures/trade/cancel_all_orders", {"symbol": symbol}, {"error": str(exc)}, "error")
                results.append({"symbol": symbol, "requested": False})
    except LiveTradingBlocked:
        pass
    db.session.commit()
    return {"kill_switch_active": True, "new_orders_blocked": True, "cancellations": results}
