import json
from app.extensions import db
from app.models.base import TimestampMixin


class LiveOrderLog(TimestampMixin, db.Model):
    __tablename__ = "live_order_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    endpoint = db.Column(db.String(255), nullable=False)
    request_payload = db.Column(db.Text, nullable=False)
    response_payload = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), nullable=False, index=True)

    @classmethod
    def create(cls, user_id, endpoint, request_payload, response_payload, status):
        return cls(user_id=user_id, endpoint=endpoint, request_payload=json.dumps(request_payload, default=str), response_payload=json.dumps(response_payload, default=str), status=status)
