from app.extensions import db
from app.models.base import TimestampMixin


class TokenBlocklist(TimestampMixin, db.Model):
    __tablename__ = "token_blocklist"

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, index=True, unique=True)
