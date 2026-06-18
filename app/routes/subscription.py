from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.services.subscription_service import get_current_subscription, list_plans
from app.utils.decorators import current_user
from app.utils.responses import error_response, success_response

subscription_bp = Blueprint("subscription", __name__)


@subscription_bp.get("/plans")
def plans():
    return success_response({"plans": list_plans()})


@subscription_bp.get("/current")
@jwt_required()
def current_subscription():
    user = current_user()
    if user is None or not user.is_active:
        return error_response("User not found or inactive", 401)

    subscription = get_current_subscription(user.id)
    return success_response({"subscription": subscription.to_dict() if subscription else None})
