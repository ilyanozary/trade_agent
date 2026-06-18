from __future__ import annotations

from decimal import Decimal


def calculate_ema(values: list[float], period: int) -> float:
    if len(values) < period:
        raise ValueError(f"At least {period} values are required")
    multiplier = 2 / (period + 1)
    ema = sum(values[:period]) / period
    for value in values[period:]:
        ema = (value - ema) * multiplier + ema
    return ema


def calculate_rsi(values: list[float], period: int = 14) -> float:
    if len(values) <= period:
        raise ValueError(f"At least {period + 1} values are required")
    changes = [current - previous for previous, current in zip(values, values[1:])]
    gains = [max(change, 0) for change in changes]
    losses = [abs(min(change, 0)) for change in changes]
    average_gain = sum(gains[:period]) / period
    average_loss = sum(losses[:period]) / period
    for gain, loss in zip(gains[period:], losses[period:]):
        average_gain = ((average_gain * (period - 1)) + gain) / period
        average_loss = ((average_loss * (period - 1)) + loss) / period
    if average_loss == 0:
        return 100.0
    return 100 - (100 / (1 + average_gain / average_loss))


def calculate_atr(candles: list[dict], period: int = 14) -> float:
    if len(candles) <= period:
        raise ValueError(f"At least {period + 1} candles are required")
    true_ranges = []
    for previous, current in zip(candles, candles[1:]):
        true_ranges.append(
            max(
                current["high"] - current["low"],
                abs(current["high"] - previous["close"]),
                abs(current["low"] - previous["close"]),
            )
        )
    atr = sum(true_ranges[:period]) / period
    for value in true_ranges[period:]:
        atr = ((atr * (period - 1)) + value) / period
    return atr


def calculate_directional_confidence(summary: dict, side: str) -> int:
    """Score setup strength continuously while entry rules remain strict."""
    price = float(summary["latest_price"])
    ema50 = float(summary["ema50"])
    ema200 = float(summary["ema200"])
    rsi = float(summary["rsi14"])
    atr = max(float(summary["atr14"]), price * 0.000001)
    volume = float(summary["volume"])
    average_volume = max(float(summary["average_volume"]), 0.000001)

    if side == "LONG":
        trend_matches = ema50 > ema200
        price_matches = price > ema50
        rsi_matches = 50 <= rsi <= 70
        rsi_center = 60
    else:
        trend_matches = ema50 < ema200
        price_matches = price < ema50
        rsi_matches = 30 <= rsi <= 50
        rsi_center = 40

    trend_points = 15 * min(abs(ema50 - ema200) / (atr * 3), 1) if trend_matches else 0
    price_points = 15 * min(abs(price - ema50) / (atr * 2), 1) if price_matches else 0
    rsi_quality = max(0, 1 - abs(rsi - rsi_center) / 10)
    rsi_points = 7.5 + (7.5 * rsi_quality) if rsi_matches else 0
    volume_ratio = volume / average_volume
    volume_points = min(10, max(0, (volume_ratio - 1) * 20))
    return min(85, round(50 + trend_points + price_points + rsi_points + volume_points))


def generate_strategy_signal(symbol: str, candles: list[dict]) -> dict:
    if len(candles) < 200:
        raise ValueError("At least 200 candles are required for EMA200")

    closes = [float(candle["close"]) for candle in candles]
    volumes = [float(candle["volume"]) for candle in candles]
    latest_price = closes[-1]
    ema50 = calculate_ema(closes, 50)
    ema200 = calculate_ema(closes, 200)
    rsi14 = calculate_rsi(closes, 14)
    atr14 = calculate_atr(candles, 14)
    volume = volumes[-1]
    average_volume = sum(volumes[-20:]) / min(20, len(volumes))

    long_checks = [ema50 > ema200, latest_price > ema50, 50 <= rsi14 <= 70]
    short_checks = [ema50 < ema200, latest_price < ema50, 30 <= rsi14 <= 50]
    score_summary = {
        "latest_price": latest_price,
        "ema50": ema50,
        "ema200": ema200,
        "rsi14": rsi14,
        "atr14": atr14,
        "volume": volume,
        "average_volume": average_volume,
    }
    long_confidence = calculate_directional_confidence(score_summary, "LONG")
    short_confidence = calculate_directional_confidence(score_summary, "SHORT")
    action = "LONG" if all(long_checks) else "SHORT" if all(short_checks) else "HOLD"
    confidence = long_confidence if action == "LONG" else short_confidence if action == "SHORT" else max(long_confidence, short_confidence)
    setup_bias = "LONG" if long_confidence > short_confidence else "SHORT" if short_confidence > long_confidence else "NEUTRAL"

    if action == "LONG":
        stop_loss = latest_price - atr14
        take_profit = latest_price + (atr14 * 2)
    elif action == "SHORT":
        stop_loss = latest_price + atr14
        take_profit = latest_price - (atr14 * 2)
    else:
        stop_loss = latest_price
        take_profit = latest_price

    reason = (
        f"{action}: EMA50={ema50:.4f}, EMA200={ema200:.4f}, "
        f"price={latest_price:.4f}, RSI14={rsi14:.2f}, "
        f"volume {'above' if volume > average_volume else 'below'} average; "
        f"LONG score={long_confidence}, SHORT score={short_confidence}, bias={setup_bias}."
    )
    return {
        "action": action,
        "confidence_base": confidence,
        "entry_price": latest_price,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "strategy_reason": reason,
        "directional_confidence": {
            "long": long_confidence,
            "short": short_confidence,
            "bias": setup_bias,
        },
        "market_summary": {
            "symbol": symbol,
            "latest_price": latest_price,
            "ema50": ema50,
            "ema200": ema200,
            "rsi14": rsi14,
            "atr14": atr14,
            "volume": volume,
            "average_volume": average_volume,
        },
    }


def build_trade_scenarios(
    strategy_signal: dict,
    balance_usdt,
    risk_per_trade_percent,
    leverage: int,
    confidence_threshold: int,
) -> dict:
    """Compare hypothetical LONG and SHORT plans without executing either one."""
    summary = strategy_signal["market_summary"]
    entry = Decimal(str(summary["latest_price"]))
    atr = Decimal(str(summary["atr14"]))
    balance = Decimal(str(balance_usdt))
    risk_percent = Decimal(str(risk_per_trade_percent))
    risk_budget = balance * risk_percent / Decimal("100")
    volume_confirmed = summary["volume"] > summary["average_volume"]

    definitions = {
        "LONG": [
            ("EMA50 above EMA200", summary["ema50"] > summary["ema200"]),
            ("Price above EMA50", summary["latest_price"] > summary["ema50"]),
            ("RSI between 50 and 70", 50 <= summary["rsi14"] <= 70),
        ],
        "SHORT": [
            ("EMA50 below EMA200", summary["ema50"] < summary["ema200"]),
            ("Price below EMA50", summary["latest_price"] < summary["ema50"]),
            ("RSI between 30 and 50", 30 <= summary["rsi14"] <= 50),
        ],
    }

    scenarios = {}
    for side, checks in definitions.items():
        confidence = calculate_directional_confidence(summary, side)
        stop_loss = entry - atr if side == "LONG" else entry + atr
        take_profit = entry + (atr * 2) if side == "LONG" else entry - (atr * 2)
        quantity = risk_budget / atr if atr > 0 else Decimal("0")
        margin = quantity * entry / Decimal(str(leverage)) if leverage > 0 else Decimal("0")
        if margin > balance and entry > 0:
            margin = balance
            quantity = margin * Decimal(str(leverage)) / entry
        max_loss = atr * quantity
        target_profit = atr * Decimal("2") * quantity
        target_return_percent = target_profit / margin * Decimal("100") if margin else Decimal("0")
        conditions_met = sum(1 for _label, passed in checks if passed)

        scenarios[side.lower()] = {
            "side": side,
            "entry_price": float(entry),
            "stop_loss": float(stop_loss),
            "take_profit": float(take_profit),
            "quantity": float(quantity),
            "margin_usdt": float(margin),
            "risk_usdt": float(max_loss),
            "target_profit_usdt": float(target_profit),
            "target_return_percent": float(target_return_percent),
            "risk_reward_ratio": 2,
            "confidence": confidence,
            "confidence_threshold": confidence_threshold,
            "conditions_met": conditions_met,
            "conditions_total": len(checks),
            "volume_confirmed": volume_confirmed,
            "eligible": all(passed for _label, passed in checks) and confidence >= confidence_threshold,
            "conditions": [{"label": label, "passed": passed} for label, passed in checks],
        }

    preferred = "LONG" if scenarios["long"]["confidence"] > scenarios["short"]["confidence"] else "SHORT"
    if scenarios["long"]["confidence"] == scenarios["short"]["confidence"]:
        preferred = "HOLD"
    return {
        "preferred_scenario": preferred,
        "note": "Counterfactual simulation only; neither scenario is executed from this comparison.",
        **scenarios,
    }
