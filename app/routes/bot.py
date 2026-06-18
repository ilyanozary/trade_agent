from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models import BotProfile
from app.services.market_data_service import get_supported_symbols
from app.utils.decorators import current_user, subscription_required
from app.utils.responses import error_response, success_response
from app.utils.validators import BotProfileSchema, validate_json

bot_bp = Blueprint("bot", __name__)

RISK_DEFAULTS = {
    "conservative": {"risk_per_trade_percent": 0.5, "max_daily_loss_percent": 2},
    "balanced": {"risk_per_trade_percent": 1, "max_daily_loss_percent": 3},
    "aggressive": {"risk_per_trade_percent": 2, "max_daily_loss_percent": 5},
}


def get_or_create_profile(user_id: int) -> BotProfile:
    profile = BotProfile.query.filter_by(user_id=user_id).first()
    if profile is None:
        profile = BotProfile(user_id=user_id)
        db.session.add(profile)
        db.session.commit()
    return profile


def apply_profile_payload(profile: BotProfile, payload: dict) -> None:
    risk_profile = payload.get("risk_profile")
    if payload.get("symbol") and payload["symbol"] not in get_supported_symbols():
        supported = ", ".join(sorted(get_supported_symbols()))
        raise ValueError(f"Symbol is unavailable for the active provider. Choose: {supported}")
    if risk_profile:
        profile.risk_profile = risk_profile
        defaults = RISK_DEFAULTS[risk_profile]
        payload.setdefault("risk_per_trade_percent", defaults["risk_per_trade_percent"])
        payload.setdefault("max_daily_loss_percent", defaults["max_daily_loss_percent"])

    for field in [
        "mode",
        "symbol",
        "is_enabled",
        "confidence_threshold",
        "max_daily_loss_percent",
        "risk_per_trade_percent",
        "max_leverage",
        "max_open_positions",
    ]:
        if field in payload:
            setattr(profile, field, payload[field])


@bot_bp.get("/profile")
@jwt_required()
def get_profile():
    user = current_user()
    if user is None or not user.is_active:
        return error_response("User not found or inactive", 401)

    profile = get_or_create_profile(user.id)
    if profile.symbol not in get_supported_symbols():
        profile.symbol = "BTCUSDT"
        db.session.commit()
    return success_response({"bot_profile": profile.to_dict(), "supported_symbols": sorted(get_supported_symbols())})


@bot_bp.post("/profile")
@subscription_required
def create_profile():
    user = current_user()
    payload = validate_json(BotProfileSchema(), request.get_json(silent=True))
    profile = get_or_create_profile(user.id)
    try:
        apply_profile_payload(profile, payload)
    except ValueError as exc:
        return error_response(str(exc), 422)
    db.session.commit()
    return success_response({"bot_profile": profile.to_dict()}, "Bot profile saved")


@bot_bp.patch("/profile")
@subscription_required
def update_profile():
    user = current_user()
    payload = validate_json(BotProfileSchema(partial=True), request.get_json(silent=True))
    profile = get_or_create_profile(user.id)
    try:
        apply_profile_payload(profile, payload)
    except ValueError as exc:
        return error_response(str(exc), 422)
    db.session.commit()
    return success_response({"bot_profile": profile.to_dict()}, "Bot profile updated")
