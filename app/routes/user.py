from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.utils.decorators import current_user
from app.utils.responses import error_response, success_response

user_bp = Blueprint("user", __name__)


@user_bp.get("/profile")
@jwt_required()
def profile():
    user = current_user()
    if user is None or not user.is_active:
        return error_response("User not found or inactive", 401)
    return success_response({"user": user.to_dict()})
