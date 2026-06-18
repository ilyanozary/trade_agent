from flask import Flask
from flask_jwt_extended import get_jwt
from marshmallow import ValidationError

from app.config import Config
from app.cli import register_cli
from app.extensions import cors, db, jwt, migrate
from app.models import TokenBlocklist
from app.routes.admin import admin_bp
from app.routes.auth import auth_bp
from app.routes.bot import bot_bp
from app.routes.dashboard import dashboard_bp
from app.routes.payment import payment_bp
from app.routes.paper import paper_bp
from app.routes.subscription import subscription_bp
from app.routes.user import user_bp
from app.routes.exchange import exchange_bp
from app.routes.live import live_bp
from app.utils.responses import error_response


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    register_blueprints(app)
    register_error_handlers(app)
    register_jwt_handlers()
    register_cli(app)

    return app


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(user_bp, url_prefix="/api/user")
    app.register_blueprint(subscription_bp, url_prefix="/api/subscriptions")
    app.register_blueprint(payment_bp, url_prefix="/api/payments")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(bot_bp, url_prefix="/api/bot")
    app.register_blueprint(paper_bp, url_prefix="/api/paper")
    app.register_blueprint(exchange_bp, url_prefix="/api/exchange")
    app.register_blueprint(live_bp, url_prefix="/api/live")


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError):
        return error_response("Validation failed", 422, details=error.messages)

    @app.errorhandler(404)
    def handle_not_found(_error):
        return error_response("Resource not found", 404)

    @app.errorhandler(500)
    def handle_internal_error(_error):
        return error_response("Internal server error", 500)


def register_jwt_handlers() -> None:
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(_jwt_header, jwt_payload: dict) -> bool:
        token = TokenBlocklist.query.filter_by(jti=jwt_payload["jti"]).first()
        return token is not None

    @jwt.revoked_token_loader
    def revoked_token_callback(_jwt_header, _jwt_payload):
        return error_response("Token has been revoked", 401)

    @jwt.unauthorized_loader
    def missing_token_callback(reason: str):
        return error_response(reason, 401)

    @jwt.invalid_token_loader
    def invalid_token_callback(reason: str):
        return error_response(reason, 422)

    @jwt.expired_token_loader
    def expired_token_callback(_jwt_header, _jwt_payload):
        return error_response("Token has expired", 401)
