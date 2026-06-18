from decimal import Decimal

from app.extensions import db
from app.models.base import TimestampMixin


class PaperAccount(TimestampMixin, db.Model):
    __tablename__ = "paper_accounts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False, index=True)
    balance_usdt = db.Column(db.Numeric(18, 8), nullable=False, default=Decimal("10000"))
    equity_usdt = db.Column(db.Numeric(18, 8), nullable=False, default=Decimal("10000"))
    realized_pnl = db.Column(db.Numeric(18, 8), nullable=False, default=Decimal("0"))
    unrealized_pnl = db.Column(db.Numeric(18, 8), nullable=False, default=Decimal("0"))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "balance_usdt": float(self.balance_usdt),
            "equity_usdt": float(self.equity_usdt),
            "realized_pnl": float(self.realized_pnl),
            "unrealized_pnl": float(self.unrealized_pnl),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
