from decimal import Decimal

from app.extensions import db
from app.models.base import TimestampMixin


class Payment(TimestampMixin, db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    plan_name = db.Column(db.String(80), nullable=False)
    amount_usdt = db.Column(db.Numeric(12, 2), nullable=False)
    network = db.Column(db.String(20), nullable=False, default="TRC20")
    wallet_address = db.Column(db.String(255), nullable=False)
    tx_hash = db.Column(db.String(255), nullable=True, index=True)
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    confirmed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        amount = self.amount_usdt
        if isinstance(amount, Decimal):
            amount = float(amount)

        return {
            "id": self.id,
            "user_id": self.user_id,
            "plan_name": self.plan_name,
            "amount_usdt": amount,
            "network": self.network,
            "wallet_address": self.wallet_address,
            "tx_hash": self.tx_hash,
            "status": self.status,
            "expires_at": self.expires_at.isoformat(),
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
