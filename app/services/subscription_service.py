from datetime import UTC, datetime, timedelta

from flask import current_app

from app.extensions import db
from app.models import Subscription
from app.models.base import ensure_utc


def get_plan(plan_name: str) -> dict | None:
    return next(
        (plan for plan in current_app.config["SUBSCRIPTION_PLANS"] if plan["name"] == plan_name),
        None,
    )


def list_plans() -> list[dict]:
    return current_app.config["SUBSCRIPTION_PLANS"]


def get_current_subscription(user_id: int) -> Subscription | None:
    now = datetime.now(UTC)
    subscription = (
        Subscription.query.filter_by(user_id=user_id, status="active")
        .order_by(Subscription.expires_at.desc())
        .first()
    )
    if subscription and ensure_utc(subscription.expires_at) <= now:
        subscription.status = "expired"
        db.session.commit()
        return None
    return subscription


def create_or_extend_subscription(user_id: int, plan_name: str, duration_days: int) -> Subscription:
    now = datetime.now(UTC)
    subscription = (
        Subscription.query.filter_by(user_id=user_id, status="active")
        .order_by(Subscription.expires_at.desc())
        .first()
    )

    if subscription and ensure_utc(subscription.expires_at) > now:
        subscription.plan_name = plan_name
        subscription.expires_at = ensure_utc(subscription.expires_at) + timedelta(days=duration_days)
        return subscription

    if subscription and ensure_utc(subscription.expires_at) <= now:
        subscription.status = "expired"

    subscription = Subscription(
        user_id=user_id,
        plan_name=plan_name,
        status="active",
        started_at=now,
        expires_at=now + timedelta(days=duration_days),
    )
    db.session.add(subscription)
    return subscription
