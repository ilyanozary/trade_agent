from datetime import UTC, datetime, timedelta

from flask import Blueprint, current_app, request
from flask_jwt_extended import create_access_token, get_jwt, jwt_required

from app.extensions import db
from app.models import BotProfile, Subscription, TokenBlocklist, User
from app.services.paper_trading_engine import get_or_create_paper_account
from app.utils.decorators import current_user
from app.utils.responses import error_response, success_response
from app.utils.validators import LoginSchema, RegisterSchema, validate_json

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    payload = validate_json(RegisterSchema(), request.get_json(silent=True))
    username = payload["username"].lower().strip()
    email = payload.get("email")
    email = email.lower().strip() if email else None

    if current_app.config["DEVELOPMENT_MODE"] and (
        username != current_app.config["DEV_USERNAME"].lower()
        or payload["password"] != current_app.config["DEV_PASSWORD"]
    ):
        return error_response("Use the configured development username and password", 403)

    if User.query.filter_by(username=username).first():
        return error_response("Username is already registered", 409)
    if email and User.query.filter_by(email=email).first():
        return error_response("Email is already registered", 409)

    user = User(username=username, email=email, full_name=payload["full_name"].strip())
    user.set_password(payload["password"])
    db.session.add(user)
    db.session.flush()

    if current_app.config["DEVELOPMENT_MODE"]:
        now = datetime.now(UTC)
        db.session.add(
            Subscription(
                user_id=user.id,
                plan_name="Development",
                status="active",
                started_at=now,
                expires_at=now + timedelta(days=3650),
            )
        )
        db.session.add(
            BotProfile(
                user_id=user.id,
                mode="paper",
                risk_profile="balanced",
                symbol="BTCUSDT",
                is_enabled=True,
                confidence_threshold=current_app.config["PAPER_CONFIDENCE_THRESHOLD"],
                max_daily_loss_percent=3,
                risk_per_trade_percent=1,
            )
        )
        get_or_create_paper_account(user.id)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return success_response({"user": user.to_dict(), "access_token": access_token}, "User registered", 201)


@auth_bp.post("/login")
def login():
    payload = validate_json(LoginSchema(), request.get_json(silent=True))
    username = payload["username"].lower().strip()
    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(payload["password"]):
        return error_response("Invalid username or password", 401)
    if not user.is_active:
        return error_response("Account is inactive", 403)

    access_token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return success_response({"user": user.to_dict(), "access_token": access_token}, "Logged in")


@auth_bp.get("/me")
@jwt_required()
def me():
    user = current_user()
    if user is None or not user.is_active:
        return error_response("User not found or inactive", 401)
    return success_response({"user": user.to_dict()})


@auth_bp.post("/logout")
@jwt_required()
def logout():
    jwt_payload = get_jwt()
    db.session.add(TokenBlocklist(jti=jwt_payload["jti"]))
    db.session.commit()
    return success_response(message="Logged out")
