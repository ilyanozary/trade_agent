from datetime import UTC, datetime
from app.extensions import db
from app.models.base import TimestampMixin


class LiveRiskState(TimestampMixin, db.Model):
    __tablename__ = "live_risk_states"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False, index=True)
    trading_date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(UTC).date())
    daily_realized_pnl = db.Column(db.Numeric(18, 8), nullable=False, default=0)
    starting_balance = db.Column(db.Numeric(18, 8), nullable=True)
    kill_switch_active = db.Column(db.Boolean, nullable=False, default=False)
    last_reason = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {"daily_realized_pnl": float(self.daily_realized_pnl), "starting_balance": float(self.starting_balance) if self.starting_balance is not None else None, "kill_switch_active": self.kill_switch_active, "last_reason": self.last_reason}
