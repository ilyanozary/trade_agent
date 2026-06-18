from datetime import UTC, datetime
from functools import wraps

from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import Subscription, User
from app.models.base import ensure_utc
from app.utils.responses import error_response


def current_user() -> User | None:
    identity = get_jwt_identity()
    if identity is None:
        return None
    return db.session.get(User, int(identity))


def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = current_user()
        if user is None or not user.is_active:
            return error_response("User not found or inactive", 401)
        if user.role != "admin":
            return error_response("Admin access required", 403)
        return fn(*args, **kwargs)

    return wrapper


def subscription_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = current_user()
        if user is None or not user.is_active:
            return error_response("User not found or inactive", 401)

        subscription = (
            Subscription.query.filter_by(user_id=user.id, status="active")
            .order_by(Subscription.expires_at.desc())
            .first()
        )
        if subscription is None or ensure_utc(subscription.expires_at) <= datetime.now(UTC):
            return error_response("Active subscription required", 402)

        return fn(*args, **kwargs)

    return wrapper
