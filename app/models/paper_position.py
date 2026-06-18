from app.extensions import db
from app.models.base import TimestampMixin


class PaperPosition(TimestampMixin, db.Model):
    __tablename__ = "paper_positions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    symbol = db.Column(db.String(30), nullable=False, index=True)
    side = db.Column(db.String(10), nullable=False)
    entry_price = db.Column(db.Numeric(24, 10), nullable=False)
    current_price = db.Column(db.Numeric(24, 10), nullable=False)
    quantity = db.Column(db.Numeric(24, 10), nullable=False)
    margin_usdt = db.Column(db.Numeric(18, 8), nullable=False)
    leverage = db.Column(db.Integer, nullable=False, default=1)
    stop_loss = db.Column(db.Numeric(24, 10), nullable=False)
    take_profit = db.Column(db.Numeric(24, 10), nullable=False)
    confidence = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="open", index=True)
    opened_at = db.Column(db.DateTime(timezone=True), nullable=False)
    closed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    close_price = db.Column(db.Numeric(24, 10), nullable=True)
    pnl_usdt = db.Column(db.Numeric(18, 8), nullable=False, default=0)
    pnl_percent = db.Column(db.Numeric(12, 6), nullable=False, default=0)
    close_reason = db.Column(db.String(30), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "symbol": self.symbol,
            "side": self.side,
            "entry_price": float(self.entry_price),
            "current_price": float(self.current_price),
            "quantity": float(self.quantity),
            "margin_usdt": float(self.margin_usdt),
            "leverage": self.leverage,
            "stop_loss": float(self.stop_loss),
            "take_profit": float(self.take_profit),
            "confidence": self.confidence,
            "status": self.status,
            "opened_at": self.opened_at.isoformat(),
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "close_price": float(self.close_price) if self.close_price is not None else None,
            "pnl_usdt": float(self.pnl_usdt),
            "pnl_percent": float(self.pnl_percent),
            "close_reason": self.close_reason,
        }
