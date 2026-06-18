from app.extensions import db
from app.models.base import TimestampMixin


class ExchangeApiKey(TimestampMixin, db.Model):
    __tablename__ = "exchange_api_keys"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    exchange = db.Column(db.String(40), nullable=False, default="bitunix")
    api_key_encrypted = db.Column(db.Text, nullable=False)
    api_secret_encrypted = db.Column(db.Text, nullable=False)
    is_connected = db.Column(db.Boolean, nullable=False, default=False)
    last_validated_at = db.Column(db.DateTime(timezone=True), nullable=True)

    __table_args__ = (db.UniqueConstraint("user_id", "exchange", name="uq_user_exchange_key"),)

    def to_status_dict(self):
        return {
            "exchange": self.exchange,
            "is_connected": self.is_connected,
            "last_validated_at": self.last_validated_at.isoformat() if self.last_validated_at else None,
        }
