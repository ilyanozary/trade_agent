from __future__ import annotations

import json

import requests
from flask import current_app

SYSTEM_PROMPT = (
    "You are an AI risk filter. You validate a strategy signal but never place orders yourself. "
    "You only validate or reject a pre-generated technical trading signal. You must be conservative. "
    "You must never guarantee profit. You must not invent a trade direction. You may only confirm "
    "the provided strategy action or downgrade it to HOLD. Return valid JSON only."
)


def _fallback(strategy_signal: dict, reason: str) -> dict:
    return {
        "action": strategy_signal["action"],
        "confidence": int(strategy_signal["confidence_base"]),
        "ai_reason": reason,
    }


def validate_signal_with_ai(strategy_signal: dict) -> dict:
    api_key = current_app.config["OPENAI_API_KEY"]
    if not api_key:
        return _fallback(strategy_signal, "AI disabled; using rule-based strategy confidence.")

    summary = strategy_signal["market_summary"]
    user_prompt = f"""Analyze this paper trading signal:

Symbol: {summary['symbol']}
Latest Price: {summary['latest_price']}
EMA50: {summary['ema50']}
EMA200: {summary['ema200']}
RSI14: {summary['rsi14']}
ATR14: {summary['atr14']}
Volume: {summary['volume']}
Average Volume: {summary['average_volume']}

Strategy Action: {strategy_signal['action']}
Strategy Confidence: {strategy_signal['confidence_base']}
Entry: {strategy_signal['entry_price']}
Stop Loss: {strategy_signal['stop_loss']}
Take Profit: {strategy_signal['take_profit']}

Rules:
- If Strategy Action is LONG, return LONG or HOLD only.
- If Strategy Action is SHORT, return SHORT or HOLD only.
- If Strategy Action is HOLD, return HOLD only.
- Be conservative.
- Confidence must reflect risk quality, not profit guarantee.

Return JSON with action, confidence, and ai_reason."""

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": current_app.config["OPENAI_MODEL"],
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            },
            timeout=20,
        )
        response.raise_for_status()
        result = json.loads(response.json()["choices"][0]["message"]["content"])
        action = str(result["action"]).upper()
        confidence = int(result["confidence"])
        ai_reason = str(result["ai_reason"]).strip()[:500]
        allowed_actions = {"HOLD", strategy_signal["action"]}
        if action not in allowed_actions:
            return {
                "action": "HOLD",
                "confidence": 0,
                "ai_reason": "AI response rejected because it attempted to change trade direction.",
            }
        if not 0 <= confidence <= 100 or not ai_reason:
            raise ValueError("AI response violates signal constraints")
        confidence = min(confidence, int(strategy_signal["confidence_base"]))
        return {"action": action, "confidence": confidence, "ai_reason": ai_reason}
    except (KeyError, TypeError, ValueError, json.JSONDecodeError, requests.RequestException):
        return _fallback(strategy_signal, "AI validation failed; using rule-based strategy confidence.")
