from app.extensions import db
from app.models.base import TimestampMixin


class BotProfile(TimestampMixin, db.Model):
    __tablename__ = "bot_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False, index=True)
    mode = db.Column(db.String(20), nullable=False, default="paper")
    risk_profile = db.Column(db.String(20), nullable=False, default="balanced")
    symbol = db.Column(db.String(30), nullable=False, default="BTCUSDT")
    is_enabled = db.Column(db.Boolean, nullable=False, default=False)
    confidence_threshold = db.Column(db.Integer, nullable=False, default=70)
    max_daily_loss_percent = db.Column(db.Numeric(5, 2), nullable=False, default=3)
    risk_per_trade_percent = db.Column(db.Numeric(5, 2), nullable=False, default=1)
    live_trading_enabled = db.Column(db.Boolean, nullable=False, default=False)
    risk_disclaimer_accepted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    max_leverage = db.Column(db.Integer, nullable=False, default=2)
    max_open_positions = db.Column(db.Integer, nullable=False, default=1)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "mode": self.mode,
            "risk_profile": self.risk_profile,
            "symbol": self.symbol,
            "is_enabled": self.is_enabled,
            "confidence_threshold": self.confidence_threshold,
            "max_daily_loss_percent": float(self.max_daily_loss_percent),
            "risk_per_trade_percent": float(self.risk_per_trade_percent),
            "live_trading_enabled": self.live_trading_enabled,
            "risk_disclaimer_accepted_at": self.risk_disclaimer_accepted_at.isoformat() if self.risk_disclaimer_accepted_at else None,
            "max_leverage": self.max_leverage,
            "max_open_positions": self.max_open_positions,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
