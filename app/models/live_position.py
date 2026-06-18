from app.extensions import db
from app.models.base import TimestampMixin


class LivePosition(TimestampMixin, db.Model):
    __tablename__ = "live_positions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    exchange_position_id = db.Column(db.String(100), nullable=True, index=True)
    exchange_order_id = db.Column(db.String(100), nullable=False, index=True)
    symbol = db.Column(db.String(30), nullable=False, index=True)
    side = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Numeric(24, 10), nullable=False)
    entry_price = db.Column(db.Numeric(24, 10), nullable=True)
    stop_loss = db.Column(db.Numeric(24, 10), nullable=False)
    take_profit = db.Column(db.Numeric(24, 10), nullable=False)
    leverage = db.Column(db.Integer, nullable=False)
    confidence = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="submitted", index=True)

    def to_dict(self):
        return {"id": self.id, "symbol": self.symbol, "side": self.side, "exchange_order_id": self.exchange_order_id, "quantity": float(self.quantity), "entry_price": float(self.entry_price) if self.entry_price is not None else None, "stop_loss": float(self.stop_loss), "take_profit": float(self.take_profit), "leverage": self.leverage, "confidence": self.confidence, "status": self.status, "created_at": self.created_at.isoformat(), "updated_at": self.updated_at.isoformat()}
