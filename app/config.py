import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-too")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://tradepilot:tradepilot@localhost:5432/tradepilot_ai",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    ]

    USDT_TRC20_WALLET_ADDRESS = os.getenv("USDT_TRC20_WALLET_ADDRESS", "")
    MARKET_DATA_PROVIDER = os.getenv("MARKET_DATA_PROVIDER", "mock").lower()
    BITUNIX_FUTURES_BASE_URL = os.getenv("BITUNIX_FUTURES_BASE_URL", "https://fapi.bitunix.com")
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
    LIVE_TRADING_API_ENABLED = os.getenv("LIVE_TRADING_API_ENABLED", "false").lower() == "true"
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    PAPER_TRADING_INITIAL_BALANCE = float(os.getenv("PAPER_TRADING_INITIAL_BALANCE", "10000"))
    PAPER_TRADING_DEFAULT_LEVERAGE = int(os.getenv("PAPER_TRADING_DEFAULT_LEVERAGE", "1"))
    PAPER_CONFIDENCE_THRESHOLD = int(os.getenv("PAPER_CONFIDENCE_THRESHOLD", "70"))
    DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"
    DEV_USERNAME = os.getenv("DEV_USERNAME", "ilyanozary")
    DEV_PASSWORD = os.getenv("DEV_PASSWORD", "ilyalm10")

    SUBSCRIPTION_PLANS = [
        {
            "name": "Starter",
            "price_usdt": 25,
            "duration_days": 30,
            "features": [
                "Paper Trading",
                "AI Market Analysis",
                "Trade Journal",
                "Risk Dashboard",
            ],
        },
        {
            "name": "Pro",
            "price_usdt": 40,
            "duration_days": 30,
            "features": [
                "Everything in Starter",
                "Extended Paper Trading Limits",
                "Advanced AI Confidence Analysis",
                "Priority Bot Execution",
                "Advanced Risk Settings",
            ],
        },
    ]
