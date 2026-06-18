from app.extensions import db
from app.models.base import TimestampMixin


class LiveTrade(TimestampMixin, db.Model):
    __tablename__ = "live_trades"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    symbol = db.Column(db.String(30), nullable=False, index=True)
    side = db.Column(db.String(10), nullable=False)
    exchange_order_id = db.Column(db.String(100), nullable=False, index=True)
    entry_price = db.Column(db.Numeric(24, 10), nullable=True)
    exit_price = db.Column(db.Numeric(24, 10), nullable=True)
    quantity = db.Column(db.Numeric(24, 10), nullable=False)
    pnl_usdt = db.Column(db.Numeric(18, 8), nullable=True)
    status = db.Column(db.String(30), nullable=False)

    def to_dict(self):
        return {"id": self.id, "symbol": self.symbol, "side": self.side, "exchange_order_id": self.exchange_order_id, "entry_price": float(self.entry_price) if self.entry_price is not None else None, "exit_price": float(self.exit_price) if self.exit_price is not None else None, "quantity": float(self.quantity), "pnl_usdt": float(self.pnl_usdt) if self.pnl_usdt is not None else None, "status": self.status, "created_at": self.created_at.isoformat(), "updated_at": self.updated_at.isoformat()}
