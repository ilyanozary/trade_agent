from app.extensions import db
from app.models.base import TimestampMixin


class PaperTrade(TimestampMixin, db.Model):
    __tablename__ = "paper_trades"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    symbol = db.Column(db.String(30), nullable=False, index=True)
    side = db.Column(db.String(10), nullable=False)
    entry_price = db.Column(db.Numeric(24, 10), nullable=False)
    exit_price = db.Column(db.Numeric(24, 10), nullable=False)
    quantity = db.Column(db.Numeric(24, 10), nullable=False)
    margin_usdt = db.Column(db.Numeric(18, 8), nullable=False)
    leverage = db.Column(db.Integer, nullable=False)
    stop_loss = db.Column(db.Numeric(24, 10), nullable=False)
    take_profit = db.Column(db.Numeric(24, 10), nullable=False)
    confidence = db.Column(db.Integer, nullable=False)
    pnl_usdt = db.Column(db.Numeric(18, 8), nullable=False)
    pnl_percent = db.Column(db.Numeric(12, 6), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    opened_at = db.Column(db.DateTime(timezone=True), nullable=False)
    closed_at = db.Column(db.DateTime(timezone=True), nullable=False)
    reason = db.Column(db.String(30), nullable=False)
    ai_reason = db.Column(db.Text, nullable=False, default="")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "symbol": self.symbol,
            "side": self.side,
            "entry_price": float(self.entry_price),
            "exit_price": float(self.exit_price),
            "quantity": float(self.quantity),
            "margin_usdt": float(self.margin_usdt),
            "leverage": self.leverage,
            "stop_loss": float(self.stop_loss),
            "take_profit": float(self.take_profit),
            "confidence": self.confidence,
            "pnl_usdt": float(self.pnl_usdt),
            "pnl_percent": float(self.pnl_percent),
            "status": self.status,
            "opened_at": self.opened_at.isoformat(),
            "closed_at": self.closed_at.isoformat(),
            "reason": self.reason,
            "ai_reason": self.ai_reason,
        }
