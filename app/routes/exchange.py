from datetime import UTC, datetime

from flask import Blueprint, current_app, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models import ExchangeApiKey
from app.services.bitunix_futures_client import BitunixAPIError, BitunixFuturesClient
from app.services.credential_service import decrypt_secret, encrypt_secret
from app.utils.decorators import current_user
from app.utils.responses import error_response, success_response
from app.utils.validators import ExchangeConnectSchema, validate_json

exchange_bp = Blueprint("exchange", __name__)


def _connection(user_id: int) -> ExchangeApiKey | None:
    return ExchangeApiKey.query.filter_by(user_id=user_id, exchange="bitunix").first()


def _client(connection: ExchangeApiKey) -> BitunixFuturesClient:
    return BitunixFuturesClient(current_app.config["BITUNIX_FUTURES_BASE_URL"], decrypt_secret(connection.api_key_encrypted), decrypt_secret(connection.api_secret_encrypted))


@exchange_bp.post("/bitunix/connect")
@jwt_required()
def connect():
    user = current_user()
    payload = validate_json(ExchangeConnectSchema(), request.get_json(silent=True))
    client = BitunixFuturesClient(current_app.config["BITUNIX_FUTURES_BASE_URL"], payload["api_key"], payload["api_secret"])
    try:
        client.get_account()
    except BitunixAPIError as exc:
        return error_response(f"Bitunix connection validation failed: {exc}", 422)
    connection = _connection(user.id) or ExchangeApiKey(user_id=user.id, exchange="bitunix")
    connection.api_key_encrypted = encrypt_secret(payload["api_key"])
    connection.api_secret_encrypted = encrypt_secret(payload["api_secret"])
    connection.is_connected = True
    connection.last_validated_at = datetime.now(UTC)
    db.session.add(connection)
    db.session.commit()
    return success_response({"connection": connection.to_status_dict()}, "Bitunix read-only connection validated")


@exchange_bp.get("/bitunix/status")
@jwt_required()
def status():
    user = current_user()
    connection = _connection(user.id)
    return success_response({"connection": connection.to_status_dict() if connection else {"exchange": "bitunix", "is_connected": False, "last_validated_at": None}})


@exchange_bp.delete("/bitunix/disconnect")
@jwt_required()
def disconnect():
    user = current_user()
    connection = _connection(user.id)
    if connection:
        db.session.delete(connection)
        profile = user.bot_profile
        if profile:
            profile.live_trading_enabled = False
        db.session.commit()
    return success_response(message="Bitunix disconnected")


@exchange_bp.get("/bitunix/account")
@jwt_required()
def account():
    user = current_user()
    connection = _connection(user.id)
    if not connection or not connection.is_connected:
        return error_response("Bitunix is not connected", 409)
    try:
        return success_response({"account": _client(connection).get_account()})
    except BitunixAPIError as exc:
        return error_response(str(exc), 502)


@exchange_bp.get("/bitunix/positions")
@jwt_required()
def positions():
    user = current_user()
    connection = _connection(user.id)
    if not connection or not connection.is_connected:
        return error_response("Bitunix is not connected", 409)
    try:
        return success_response({"positions": _client(connection).get_positions()})
    except BitunixAPIError as exc:
        return error_response(str(exc), 502)
