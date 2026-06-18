from app.extensions import db
from app.models.base import TimestampMixin


class Subscription(TimestampMixin, db.Model):
    __tablename__ = "subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    plan_name = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")
    started_at = db.Column(db.DateTime(timezone=True), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "plan_name": self.plan_name,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
