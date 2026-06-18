from datetime import UTC, datetime, timedelta

from flask import current_app

from app.extensions import db
from app.models import Payment
from app.models.base import ensure_utc, utc_now
from app.services.subscription_service import create_or_extend_subscription, get_plan


def create_payment_invoice(user_id: int, plan_name: str) -> Payment:
    plan = get_plan(plan_name)
    if plan is None:
        raise ValueError("Unknown subscription plan")

    wallet_address = current_app.config["USDT_TRC20_WALLET_ADDRESS"]
    if not wallet_address:
        raise RuntimeError("USDT_TRC20_WALLET_ADDRESS is not configured")

    payment = Payment(
        user_id=user_id,
        plan_name=plan["name"],
        amount_usdt=plan["price_usdt"],
        network="TRC20",
        wallet_address=wallet_address,
        status="pending",
        expires_at=datetime.now(UTC) + timedelta(minutes=30),
    )
    db.session.add(payment)
    db.session.commit()
    return payment


def submit_payment_tx(payment: Payment, tx_hash: str) -> Payment:
    if payment.status not in {"pending", "submitted"}:
        raise ValueError("Payment is not accepting transaction submissions")
    if ensure_utc(payment.expires_at) <= datetime.now(UTC):
        payment.status = "expired"
        db.session.commit()
        raise ValueError("Payment invoice has expired")

    payment.tx_hash = tx_hash
    payment.status = "submitted"
    db.session.commit()
    return payment


def confirm_payment(payment: Payment) -> Payment:
    if payment.status == "confirmed":
        return payment
    if payment.status not in {"pending", "submitted"}:
        raise ValueError("Only pending or submitted payments can be confirmed")

    plan = get_plan(payment.plan_name)
    if plan is None:
        raise ValueError("Payment plan no longer exists")

    payment.status = "confirmed"
    payment.confirmed_at = utc_now()
    create_or_extend_subscription(payment.user_id, payment.plan_name, plan["duration_days"])
    db.session.commit()
    return payment


def reject_payment(payment: Payment) -> Payment:
    if payment.status == "confirmed":
        raise ValueError("Confirmed payments cannot be rejected")
    payment.status = "rejected"
    db.session.commit()
    return payment
