from flask import Blueprint

from app.models import Payment
from app.services.payment_service import confirm_payment, reject_payment
from app.utils.decorators import admin_required
from app.utils.responses import error_response, success_response

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/payments")
@admin_required
def payments():
    records = Payment.query.order_by(Payment.created_at.desc()).all()
    return success_response({"payments": [payment.to_dict() for payment in records]})


@admin_bp.post("/payments/<int:payment_id>/confirm")
@admin_required
def confirm(payment_id: int):
    payment = Payment.query.get(payment_id)
    if payment is None:
        return error_response("Payment not found", 404)
    try:
        payment = confirm_payment(payment)
    except ValueError as exc:
        return error_response(str(exc), 400)
    return success_response({"payment": payment.to_dict()}, "Payment confirmed")


@admin_bp.post("/payments/<int:payment_id>/reject")
@admin_required
def reject(payment_id: int):
    payment = Payment.query.get(payment_id)
    if payment is None:
        return error_response("Payment not found", 404)
    try:
        payment = reject_payment(payment)
    except ValueError as exc:
        return error_response(str(exc), 400)
    return success_response({"payment": payment.to_dict()}, "Payment rejected")
