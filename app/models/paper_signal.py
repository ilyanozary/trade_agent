from app.extensions import db
from app.models.base import TimestampMixin


class PaperSignal(TimestampMixin, db.Model):
    __tablename__ = "paper_signals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    symbol = db.Column(db.String(30), nullable=False, index=True)
    action = db.Column(db.String(10), nullable=False)
    confidence = db.Column(db.Integer, nullable=False)
    entry_price = db.Column(db.Numeric(24, 10), nullable=False)
    stop_loss = db.Column(db.Numeric(24, 10), nullable=False)
    take_profit = db.Column(db.Numeric(24, 10), nullable=False)
    strategy_reason = db.Column(db.Text, nullable=False)
    ai_reason = db.Column(db.Text, nullable=False)
    executed = db.Column(db.Boolean, nullable=False, default=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "symbol": self.symbol,
            "action": self.action,
            "confidence": self.confidence,
            "entry_price": float(self.entry_price),
            "stop_loss": float(self.stop_loss),
            "take_profit": float(self.take_profit),
            "strategy_reason": self.strategy_reason,
            "ai_reason": self.ai_reason,
            "executed": self.executed,
            "created_at": self.created_at.isoformat(),
        }
