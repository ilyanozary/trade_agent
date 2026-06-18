from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from flask import current_app

from app.extensions import db
from app.models import BotProfile, PaperAccount, PaperPosition, PaperSignal, PaperTrade
from app.services.ai_signal_service import validate_signal_with_ai
from app.services.market_data_service import get_candles, get_latest_price, get_supported_symbols, validate_provider_symbol, validate_symbol
from app.services.strategy_engine import build_trade_scenarios, generate_strategy_signal

# This module is paper trading simulation only. It does not place real exchange orders.

ZERO = Decimal("0")


def as_decimal(value) -> Decimal:
    return Decimal(str(value))


def get_or_create_paper_account(user_id: int) -> PaperAccount:
    account = PaperAccount.query.filter_by(user_id=user_id).first()
    if account is None:
        initial_balance = as_decimal(current_app.config["PAPER_TRADING_INITIAL_BALANCE"])
        account = PaperAccount(
            user_id=user_id,
            balance_usdt=initial_balance,
            equity_usdt=initial_balance,
            realized_pnl=ZERO,
            unrealized_pnl=ZERO,
        )
        db.session.add(account)
        db.session.flush()
    return account


def calculate_position_pnl(position: PaperPosition, price) -> Decimal:
    current = as_decimal(price)
    entry = as_decimal(position.entry_price)
    quantity = as_decimal(position.quantity)
    difference = current - entry if position.side == "LONG" else entry - current
    return difference * quantity


def refresh_account_totals(account: PaperAccount) -> None:
    positions = PaperPosition.query.filter_by(user_id=account.user_id, status="open").all()
    unrealized = sum((as_decimal(position.pnl_usdt) for position in positions), ZERO)
    locked_margin = sum((as_decimal(position.margin_usdt) for position in positions), ZERO)
    account.unrealized_pnl = unrealized
    account.equity_usdt = as_decimal(account.balance_usdt) + locked_margin + unrealized


def _position_geometry_is_valid(side: str, entry: Decimal, stop: Decimal, target: Decimal) -> bool:
    if side == "LONG":
        return stop < entry < target
    if side == "SHORT":
        return target < entry < stop
    return False


def open_paper_position(
    *,
    user_id: int,
    symbol: str,
    side: str,
    entry_price,
    stop_loss,
    take_profit,
    confidence: int,
    margin_usdt=None,
    leverage: int | None = None,
    risk_per_trade_percent=None,
) -> PaperPosition:
    symbol = validate_symbol(symbol)
    side = side.upper()
    entry = as_decimal(entry_price)
    stop = as_decimal(stop_loss)
    target = as_decimal(take_profit)
    leverage = leverage or current_app.config["PAPER_TRADING_DEFAULT_LEVERAGE"]

    if leverage < 1 or leverage > 100:
        raise ValueError("Leverage must be between 1 and 100")
    if not _position_geometry_is_valid(side, entry, stop, target):
        raise ValueError("Stop loss and take profit are invalid for the selected side")
    if not 0 <= confidence <= 100:
        raise ValueError("Confidence must be between 0 and 100")
    if PaperPosition.query.filter_by(user_id=user_id, symbol=symbol, status="open").first():
        raise ValueError("An open position already exists for this symbol")

    account = get_or_create_paper_account(user_id)
    available_balance = as_decimal(account.balance_usdt)
    if available_balance <= ZERO:
        raise ValueError("Paper account has no available balance")

    if margin_usdt is not None:
        margin = as_decimal(margin_usdt)
        if margin <= ZERO or margin > available_balance:
            raise ValueError("Margin must be positive and cannot exceed available balance")
        quantity = (margin * leverage) / entry
    else:
        risk_percent = as_decimal(risk_per_trade_percent)
        if risk_percent <= ZERO or risk_percent > Decimal("100"):
            raise ValueError("Risk per trade percent must be between 0 and 100")
        stop_distance = abs(entry - stop)
        if stop_distance <= ZERO:
            raise ValueError("Stop distance must be greater than zero")
        risk_amount = available_balance * risk_percent / Decimal("100")
        quantity = risk_amount / stop_distance
        margin = quantity * entry / leverage
        if margin > available_balance:
            margin = available_balance
            quantity = margin * leverage / entry

    if quantity <= ZERO:
        raise ValueError("Calculated quantity must be greater than zero")

    position = PaperPosition(
        user_id=user_id,
        symbol=symbol,
        side=side,
        entry_price=entry,
        current_price=entry,
        quantity=quantity,
        margin_usdt=margin,
        leverage=leverage,
        stop_loss=stop,
        take_profit=target,
        confidence=confidence,
        status="open",
        opened_at=datetime.now(UTC),
        pnl_usdt=ZERO,
        pnl_percent=ZERO,
    )
    account.balance_usdt = available_balance - margin
    db.session.add(position)
    db.session.flush()
    refresh_account_totals(account)
    return position


def close_paper_position(position: PaperPosition, close_price, reason: str) -> PaperTrade:
    if position.status != "open":
        raise ValueError("Position is already closed")
    if reason not in {"TAKE_PROFIT", "STOP_LOSS", "MANUAL", "ENGINE"}:
        raise ValueError("Invalid close reason")

    account = get_or_create_paper_account(position.user_id)
    price = as_decimal(close_price)
    pnl = calculate_position_pnl(position, price)
    margin = as_decimal(position.margin_usdt)
    pnl_percent = (pnl / margin * Decimal("100")) if margin else ZERO
    closed_at = datetime.now(UTC)

    position.current_price = price
    position.close_price = price
    position.closed_at = closed_at
    position.pnl_usdt = pnl
    position.pnl_percent = pnl_percent
    position.close_reason = reason
    position.status = "closed"

    latest_signal = (
        PaperSignal.query.filter_by(user_id=position.user_id, symbol=position.symbol, executed=True)
        .order_by(PaperSignal.created_at.desc())
        .first()
    )
    trade = PaperTrade(
        user_id=position.user_id,
        symbol=position.symbol,
        side=position.side,
        entry_price=position.entry_price,
        exit_price=price,
        quantity=position.quantity,
        margin_usdt=position.margin_usdt,
        leverage=position.leverage,
        stop_loss=position.stop_loss,
        take_profit=position.take_profit,
        confidence=position.confidence,
        pnl_usdt=pnl,
        pnl_percent=pnl_percent,
        status="win" if pnl > ZERO else "loss" if pnl < ZERO else "breakeven",
        opened_at=position.opened_at,
        closed_at=closed_at,
        reason=reason,
        ai_reason=latest_signal.ai_reason if latest_signal else "Manual paper position.",
    )
    account.balance_usdt = as_decimal(account.balance_usdt) + margin + pnl
    account.realized_pnl = as_decimal(account.realized_pnl) + pnl
    db.session.add(trade)
    db.session.flush()
    refresh_account_totals(account)
    return trade


def monitor_open_positions(user_id: int) -> list[dict]:
    account = get_or_create_paper_account(user_id)
    positions = PaperPosition.query.filter_by(user_id=user_id, status="open").all()
    events = []

    for position in positions:
        if position.symbol not in get_supported_symbols():
            events.append({
                "position_id": position.id,
                "closed": False,
                "skipped": True,
                "reason": f"{position.symbol} is unavailable from the active market data provider",
            })
            continue
        price = as_decimal(get_latest_price(position.symbol))
        position.current_price = price
        position.pnl_usdt = calculate_position_pnl(position, price)
        margin = as_decimal(position.margin_usdt)
        position.pnl_percent = position.pnl_usdt / margin * Decimal("100") if margin else ZERO

        close_reason = None
        if position.side == "LONG":
            if price >= as_decimal(position.take_profit):
                close_reason = "TAKE_PROFIT"
            elif price <= as_decimal(position.stop_loss):
                close_reason = "STOP_LOSS"
        else:
            if price <= as_decimal(position.take_profit):
                close_reason = "TAKE_PROFIT"
            elif price >= as_decimal(position.stop_loss):
                close_reason = "STOP_LOSS"

        if close_reason:
            trade = close_paper_position(position, price, close_reason)
            events.append({"position_id": position.id, "closed": True, "trade": trade.to_dict()})
        else:
            events.append({"position_id": position.id, "closed": False, "pnl_usdt": float(position.pnl_usdt)})

    refresh_account_totals(account)
    db.session.commit()
    return events


def tick_paper_engine_for_user(user_id: int) -> dict:
    profile = BotProfile.query.filter_by(user_id=user_id).first()
    if profile is None or profile.mode != "paper":
        raise ValueError("Bot profile must be in paper mode")
    if not profile.is_enabled:
        raise ValueError("Paper bot is paused")

    symbol = validate_provider_symbol(profile.symbol)
    events = monitor_open_positions(user_id)
    price = get_latest_price(symbol)
    account = get_or_create_paper_account(user_id)
    positions = PaperPosition.query.filter_by(user_id=user_id, status="open").all()
    refresh_account_totals(account)
    db.session.commit()
    return {
        "success": True,
        "mode": "paper",
        "symbol": symbol,
        "latest_price": price,
        "account": account.to_dict(),
        "open_positions": [position.to_dict() for position in positions],
        "monitor_events": events,
        "timestamp": datetime.now(UTC).isoformat(),
    }


def run_paper_engine_for_user(user_id: int) -> dict:
    profile = BotProfile.query.filter_by(user_id=user_id).first()
    if profile is None:
        raise ValueError("Bot profile not found")
    if profile.mode != "paper":
        raise ValueError("Bot profile must be in paper mode")
    if not profile.is_enabled:
        raise ValueError("Bot profile is disabled")

    account = get_or_create_paper_account(user_id)
    monitor_events = monitor_open_positions(user_id)
    symbol = validate_provider_symbol(profile.symbol)
    candles = get_candles(symbol, interval="15m", limit=200)
    strategy_signal = generate_strategy_signal(symbol, candles)
    ai_signal = validate_signal_with_ai(strategy_signal)
    scenario_comparison = build_trade_scenarios(
        strategy_signal,
        account.balance_usdt,
        profile.risk_per_trade_percent,
        current_app.config["PAPER_TRADING_DEFAULT_LEVERAGE"],
        profile.confidence_threshold or current_app.config["PAPER_CONFIDENCE_THRESHOLD"],
    )

    signal = PaperSignal(
        user_id=user_id,
        symbol=symbol,
        action=ai_signal["action"],
        confidence=ai_signal["confidence"],
        entry_price=strategy_signal["entry_price"],
        stop_loss=strategy_signal["stop_loss"],
        take_profit=strategy_signal["take_profit"],
        strategy_reason=strategy_signal["strategy_reason"],
        ai_reason=ai_signal["ai_reason"],
        executed=False,
    )
    db.session.add(signal)
    db.session.flush()

    threshold = profile.confidence_threshold or current_app.config["PAPER_CONFIDENCE_THRESHOLD"]
    position = None
    reason = "Signal rejected"
    if ai_signal["action"] == "HOLD":
        reason = "Final signal is HOLD"
    elif ai_signal["confidence"] < threshold:
        reason = f"Confidence {ai_signal['confidence']} is below threshold {threshold}"
    elif PaperPosition.query.filter_by(user_id=user_id, symbol=symbol, status="open").first():
        reason = "An open position already exists for this symbol"
    else:
        try:
            position = open_paper_position(
                user_id=user_id,
                symbol=symbol,
                side=ai_signal["action"],
                entry_price=strategy_signal["entry_price"],
                stop_loss=strategy_signal["stop_loss"],
                take_profit=strategy_signal["take_profit"],
                confidence=ai_signal["confidence"],
                leverage=current_app.config["PAPER_TRADING_DEFAULT_LEVERAGE"],
                risk_per_trade_percent=profile.risk_per_trade_percent,
            )
            signal.executed = True
            reason = "Virtual paper position opened"
        except ValueError as exc:
            reason = str(exc)

    refresh_account_totals(account)
    db.session.commit()
    return {
        "success": True,
        "mode": "paper",
        "symbol": symbol,
        "strategy_signal": strategy_signal,
        "ai_signal": ai_signal,
        "scenario_comparison": scenario_comparison,
        "position_opened": position is not None,
        "position": position.to_dict() if position else None,
        "monitor_events": monitor_events,
        "reason": reason,
    }
