from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models import BotProfile, PaperAccount, PaperPosition, PaperSignal, PaperTrade
from app.services.market_data_service import get_latest_price
from app.services.paper_trading_engine import (
    close_paper_position,
    get_or_create_paper_account,
    open_paper_position,
    refresh_account_totals,
    run_paper_engine_for_user,
    tick_paper_engine_for_user,
)
from app.utils.decorators import current_user, subscription_required
from app.utils.responses import error_response, success_response
from app.utils.validators import ClosePaperPositionSchema, ManualPaperPositionSchema, validate_json

paper_bp = Blueprint("paper", __name__)

# This module is paper trading simulation only. It does not place real exchange orders.


@paper_bp.get("/account")
@jwt_required()
def get_account():
    user = current_user()
    if user is None or not user.is_active:
        return error_response("User not found or inactive", 401)
    account = get_or_create_paper_account(user.id)
    refresh_account_totals(account)
    db.session.commit()
    return success_response({"paper_account": account.to_dict()})


@paper_bp.post("/account/reset")
@subscription_required
def reset_account():
    user = current_user()
    PaperTrade.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    PaperSignal.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    PaperPosition.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    PaperAccount.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    db.session.flush()
    account = get_or_create_paper_account(user.id)
    db.session.commit()
    return success_response({"paper_account": account.to_dict()}, "Paper account reset")


@paper_bp.get("/positions")
@jwt_required()
def list_positions():
    user = current_user()
    if user is None or not user.is_active:
        return error_response("User not found or inactive", 401)
    status = request.args.get("status")
    query = PaperPosition.query.filter_by(user_id=user.id)
    if status in {"open", "closed"}:
        query = query.filter_by(status=status)
    positions = query.order_by(PaperPosition.opened_at.desc()).all()
    return success_response({"positions": [position.to_dict() for position in positions]})


@paper_bp.post("/positions/open")
@subscription_required
def manual_open_position():
    user = current_user()
    profile = BotProfile.query.filter_by(user_id=user.id).first()
    if profile is None or profile.mode != "paper":
        return error_response("Bot profile must be in paper mode", 400)
    payload = validate_json(ManualPaperPositionSchema(), request.get_json(silent=True))
    try:
        position = open_paper_position(user_id=user.id, **payload)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return error_response(str(exc), 400)
    return success_response({"position": position.to_dict()}, "Virtual paper position opened", 201)


@paper_bp.post("/positions/<int:position_id>/close")
@subscription_required
def manual_close_position(position_id: int):
    user = current_user()
    position = PaperPosition.query.filter_by(id=position_id, user_id=user.id).first()
    if position is None:
        return error_response("Paper position not found", 404)
    payload = validate_json(ClosePaperPositionSchema(), request.get_json(silent=True) or {})
    try:
        close_price = payload.get("close_price") or get_latest_price(position.symbol)
        trade = close_paper_position(position, close_price, "MANUAL")
        db.session.commit()
    except (ValueError, RuntimeError, NotImplementedError) as exc:
        db.session.rollback()
        return error_response(str(exc), 400)
    return success_response({"position": position.to_dict(), "trade": trade.to_dict()}, "Paper position closed")


@paper_bp.get("/trades")
@jwt_required()
def list_trades():
    user = current_user()
    if user is None or not user.is_active:
        return error_response("User not found or inactive", 401)
    trades = PaperTrade.query.filter_by(user_id=user.id).order_by(PaperTrade.closed_at.desc()).all()
    return success_response({"trades": [trade.to_dict() for trade in trades]})


@paper_bp.get("/signals")
@jwt_required()
def list_signals():
    user = current_user()
    if user is None or not user.is_active:
        return error_response("User not found or inactive", 401)
    signals = PaperSignal.query.filter_by(user_id=user.id).order_by(PaperSignal.created_at.desc()).all()
    return success_response({"signals": [signal.to_dict() for signal in signals]})


@paper_bp.post("/engine/run-once")
@subscription_required
def run_engine_once():
    user = current_user()
    try:
        result = run_paper_engine_for_user(user.id)
    except (ValueError, RuntimeError, NotImplementedError) as exc:
        db.session.rollback()
        return error_response(str(exc), 400)
    return jsonify(result), 200


@paper_bp.post("/engine/tick")
@subscription_required
def tick_engine():
    user = current_user()
    try:
        return jsonify(tick_paper_engine_for_user(user.id)), 200
    except (ValueError, RuntimeError, NotImplementedError) as exc:
        db.session.rollback()
        return error_response(str(exc), 400)
