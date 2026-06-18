from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.models import Payment
from app.services.payment_service import create_payment_invoice, submit_payment_tx
from app.utils.decorators import current_user
from app.utils.responses import error_response, success_response
from app.utils.validators import PaymentCreateSchema, SubmitTxSchema, validate_json

payment_bp = Blueprint("payment", __name__)


@payment_bp.post("/create")
@jwt_required()
def create_payment():
    user = current_user()
    if user is None or not user.is_active:
        return error_response("User not found or inactive", 401)

    payload = validate_json(PaymentCreateSchema(), request.get_json(silent=True))
    try:
        payment = create_payment_invoice(user.id, payload["plan_name"])
    except RuntimeError as exc:
        return error_response(str(exc), 500)
    except ValueError as exc:
        return error_response(str(exc), 400)

    return success_response({"payment": payment.to_dict()}, "Payment invoice created", 201)


@payment_bp.get("/<int:payment_id>")
@jwt_required()
def get_payment(payment_id: int):
    user = current_user()
    if user is None or not user.is_active:
        return error_response("User not found or inactive", 401)

    payment = Payment.query.filter_by(id=payment_id, user_id=user.id).first()
    if payment is None:
        return error_response("Payment not found", 404)

    return success_response({"payment": payment.to_dict()})


@payment_bp.post("/<int:payment_id>/submit-tx")
@jwt_required()
def submit_tx(payment_id: int):
    user = current_user()
    if user is None or not user.is_active:
        return error_response("User not found or inactive", 401)

    payment = Payment.query.filter_by(id=payment_id, user_id=user.id).first()
    if payment is None:
        return error_response("Payment not found", 404)

    payload = validate_json(SubmitTxSchema(), request.get_json(silent=True))
    try:
        payment = submit_payment_tx(payment, payload["tx_hash"])
    except ValueError as exc:
        return error_response(str(exc), 400)

    return success_response({"payment": payment.to_dict()}, "Transaction submitted")
