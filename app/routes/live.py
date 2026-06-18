from datetime import UTC, datetime

from flask import Blueprint, current_app, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models import BotProfile, LivePosition, LiveTrade
from app.routes.bot import get_or_create_profile
from app.services.live_trading_engine import LiveTradingBlocked, activate_kill_switch, get_or_create_risk_state, run_once
from app.utils.decorators import current_user
from app.utils.responses import error_response, success_response
from app.utils.validators import LiveEnableSchema, validate_json

live_bp = Blueprint("live", __name__)


@live_bp.get("/status")
@jwt_required()
def status():
    user = current_user()
    profile = get_or_create_profile(user.id)
    state = get_or_create_risk_state(user.id)
    db.session.commit()
    return success_response({"server_enabled": current_app.config.get("LIVE_TRADING_API_ENABLED", False), "profile": profile.to_dict(), "risk_state": state.to_dict()})


@live_bp.post("/enable")
@jwt_required()
def enable():
    if not current_app.config.get("LIVE_TRADING_API_ENABLED"):
        return error_response("Live trading is disabled by server configuration", 403)
    user = current_user()
    payload = validate_json(LiveEnableSchema(), request.get_json(silent=True))
    if not payload["accept_risk_disclaimer"]:
        return error_response("Risk disclaimer acceptance is required", 422)
    profile = get_or_create_profile(user.id)
    profile.mode = "live"
    profile.is_enabled = True
    profile.live_trading_enabled = True
    profile.risk_disclaimer_accepted_at = datetime.now(UTC)
    for field in ("max_daily_loss_percent", "risk_per_trade_percent", "max_leverage", "max_open_positions", "confidence_threshold"):
        setattr(profile, field, payload[field])
    state = get_or_create_risk_state(user.id)
    state.kill_switch_active = False
    state.last_reason = None
    db.session.commit()
    return success_response({"profile": profile.to_dict()}, "Live trading explicitly enabled")


@live_bp.post("/disable")
@jwt_required()
def disable():
    profile = get_or_create_profile(current_user().id)
    profile.live_trading_enabled = False
    profile.is_enabled = False
    db.session.commit()
    return success_response({"profile": profile.to_dict()}, "Live trading disabled")


@live_bp.post("/engine/run-once")
@jwt_required()
def engine_run_once():
    try:
        return success_response(run_once(current_user().id))
    except LiveTradingBlocked as exc:
        return error_response(str(exc), 409)


@live_bp.post("/kill-switch")
@jwt_required()
def kill_switch():
    return success_response(activate_kill_switch(current_user().id), "Kill switch activated")


@live_bp.get("/positions")
@jwt_required()
def positions():
    rows = LivePosition.query.filter_by(user_id=current_user().id).order_by(LivePosition.created_at.desc()).all()
    return success_response({"positions": [row.to_dict() for row in rows]})


@live_bp.get("/trades")
@jwt_required()
def trades():
    rows = LiveTrade.query.filter_by(user_id=current_user().id).order_by(LiveTrade.created_at.desc()).all()
    return success_response({"trades": [row.to_dict() for row in rows]})
