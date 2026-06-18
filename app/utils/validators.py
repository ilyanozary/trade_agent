import re

from marshmallow import Schema, ValidationError, fields, validate, validates

EMAIL_LENGTH = validate.Length(max=255)
PASSWORD_LENGTH = validate.Length(min=8, max=128)


class RegisterSchema(Schema):
    username = fields.String(required=True, validate=validate.Regexp(r"^[a-zA-Z0-9_]{3,80}$"))
    email = fields.Email(load_default=None, allow_none=True, validate=EMAIL_LENGTH)
    password = fields.String(required=True, validate=PASSWORD_LENGTH, load_only=True)
    full_name = fields.String(load_default="Development User", validate=validate.Length(min=2, max=160))


class LoginSchema(Schema):
    username = fields.String(required=True, validate=validate.Length(min=3, max=80))
    password = fields.String(required=True, validate=validate.Length(min=1, max=128), load_only=True)


class PaymentCreateSchema(Schema):
    plan_name = fields.String(required=True, validate=validate.OneOf(["Starter", "Pro"]))


class SubmitTxSchema(Schema):
    tx_hash = fields.String(required=True, validate=validate.Length(min=16, max=255))

    @validates("tx_hash")
    def validate_tx_hash(self, value: str, **_kwargs) -> None:
        if not re.fullmatch(r"[A-Za-z0-9]+", value):
            raise ValidationError("Transaction hash must be alphanumeric.")


class ExchangeConnectSchema(Schema):
    api_key = fields.String(required=True, validate=validate.Length(min=8, max=255), load_only=True)
    api_secret = fields.String(required=True, validate=validate.Length(min=8, max=255), load_only=True)


class BotProfileSchema(Schema):
    mode = fields.String(validate=validate.OneOf(["paper", "live"]))
    risk_profile = fields.String(validate=validate.OneOf(["conservative", "balanced", "aggressive"]))
    symbol = fields.String(
        validate=validate.OneOf(["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "AVAXUSDT", "LINKUSDT"])
    )
    is_enabled = fields.Boolean()
    confidence_threshold = fields.Integer(validate=validate.Range(min=1, max=100))
    max_daily_loss_percent = fields.Float(validate=validate.Range(min=0.1, max=100))
    risk_per_trade_percent = fields.Float(validate=validate.Range(min=0.1, max=100))
    max_leverage = fields.Integer(validate=validate.Range(min=1, max=3))
    max_open_positions = fields.Integer(validate=validate.Range(min=1, max=10))

    @validates("symbol")
    def validate_symbol(self, value: str, **_kwargs) -> None:
        if not re.fullmatch(r"[A-Z0-9]{3,30}", value):
            raise ValidationError("Symbol must use uppercase letters and numbers only.")


class LiveEnableSchema(Schema):
    accept_risk_disclaimer = fields.Boolean(required=True)
    max_daily_loss_percent = fields.Float(load_default=2, validate=validate.Range(min=0.1, max=10))
    risk_per_trade_percent = fields.Float(load_default=0.5, validate=validate.Range(min=0.1, max=5))
    max_leverage = fields.Integer(load_default=2, validate=validate.Range(min=1, max=3))
    max_open_positions = fields.Integer(load_default=1, validate=validate.Range(min=1, max=5))
    confidence_threshold = fields.Integer(load_default=75, validate=validate.Range(min=75, max=100))

class ManualPaperPositionSchema(Schema):
    symbol = fields.String(
        required=True,
        validate=validate.OneOf(["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "AVAXUSDT", "LINKUSDT"]),
    )
    side = fields.String(required=True, validate=validate.OneOf(["LONG", "SHORT"]))
    entry_price = fields.Float(required=True, validate=validate.Range(min=0.00000001))
    stop_loss = fields.Float(required=True, validate=validate.Range(min=0.00000001))
    take_profit = fields.Float(required=True, validate=validate.Range(min=0.00000001))
    margin_usdt = fields.Float(required=True, validate=validate.Range(min=0.01))
    leverage = fields.Integer(load_default=1, validate=validate.Range(min=1, max=100))
    confidence = fields.Integer(load_default=70, validate=validate.Range(min=0, max=100))


class ClosePaperPositionSchema(Schema):
    close_price = fields.Float(validate=validate.Range(min=0.00000001))


def validate_json(schema: Schema, payload: dict | None) -> dict:
    if payload is None:
        raise ValidationError({"json": ["Request body must be valid JSON."]})
    return schema.load(payload)
