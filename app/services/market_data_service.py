from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta

from flask import current_app
from app.services.bitunix_futures_client import BitunixFuturesClient
from app.services.bitunix_futures_client import SUPPORTED_BITUNIX_SYMBOLS

SUPPORTED_SYMBOLS = {"BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "AVAXUSDT", "LINKUSDT"}
MARKET_PROFILES = {
    "BTCUSDT": {"base": 100_000.0, "volatility": 0.0018, "live_wave": 0.0007, "trend": 0.00012},
    "ETHUSDT": {"base": 3_500.0, "volatility": 0.0021, "live_wave": 0.0009, "trend": 0.00010},
    "SOLUSDT": {"base": 150.0, "volatility": 0.0035, "live_wave": 0.0018, "trend": 0.00016},
    "DOGEUSDT": {"base": 0.18, "volatility": 0.0052, "live_wave": 0.0030, "trend": 0.00012},
    "AVAXUSDT": {"base": 35.0, "volatility": 0.0042, "live_wave": 0.0024, "trend": 0.00014},
    "LINKUSDT": {"base": 18.0, "volatility": 0.0032, "live_wave": 0.0017, "trend": 0.00011},
}


class MarketDataProvider(ABC):
    @abstractmethod
    def get_latest_price(self, symbol: str) -> float:
        raise NotImplementedError

    @abstractmethod
    def get_candles(self, symbol: str, interval: str = "15m", limit: int = 100) -> list[dict]:
        raise NotImplementedError


class MockMarketDataProvider(MarketDataProvider):
    """Generates deterministic, realistic OHLCV data for simulation only."""

    def get_latest_price(self, symbol: str) -> float:
        symbol = validate_symbol(symbol)
        return float(self.get_candles(symbol, limit=250)[-1]["close"])

    def get_candles(self, symbol: str, interval: str = "15m", limit: int = 100) -> list[dict]:
        symbol = validate_symbol(symbol)
        if not 1 <= limit <= 500:
            raise ValueError("Candle limit must be between 1 and 500")

        interval_minutes = {"1m": 1, "5m": 5, "15m": 15, "1h": 60}.get(interval)
        if interval_minutes is None:
            raise ValueError("Unsupported candle interval")

        bucket = int(datetime.now(UTC).timestamp() // (interval_minutes * 60))
        randomizer = random.Random(f"{symbol}:{interval}:{bucket}")
        profile = MARKET_PROFILES[symbol]
        base = profile["base"]
        price = base * (1 + 0.012 * math.sin(bucket / 29))
        start = datetime.fromtimestamp((bucket - limit + 1) * interval_minutes * 60, UTC)
        candles = []

        for index in range(limit):
            trend = profile["trend"]
            change = trend + randomizer.gauss(0, profile["volatility"])
            open_price = price
            close_price = max(0.01, open_price * (1 + change))
            spread = abs(randomizer.gauss(0.0011, 0.00045))
            high = max(open_price, close_price) * (1 + spread)
            low = min(open_price, close_price) * (1 - spread)
            volume = randomizer.uniform(700, 1800) * (1 + abs(change) * 80)
            timestamp = start + timedelta(minutes=index * interval_minutes)
            candles.append(
                {
                    "open": round(open_price, 8),
                    "high": round(high, 8),
                    "low": round(low, 8),
                    "close": round(close_price, 8),
                    "volume": round(volume, 8),
                    "timestamp": timestamp.isoformat(),
                }
            )
            price = close_price

        # Keep the active candle moving so repeated development analyses do not
        # receive an identical 15-minute close throughout the entire interval.
        now = datetime.now(UTC).timestamp()
        live_wave = profile["live_wave"]
        wave = math.sin(now / 3.2) * live_wave + math.sin(now / 11.0) * live_wave * 0.55
        active = candles[-1]
        live_close = max(0.00000001, active["close"] * (1 + wave))
        active["close"] = round(live_close, 8)
        active["high"] = round(max(active["high"], live_close), 8)
        active["low"] = round(min(active["low"], live_close), 8)
        active["volume"] = round(active["volume"] * (1 + abs(wave) * 15), 8)

        return candles


class BitunixMarketDataProvider(MarketDataProvider):
    def __init__(self):
        self.client = BitunixFuturesClient(current_app.config["BITUNIX_FUTURES_BASE_URL"])

    def get_latest_price(self, symbol: str) -> float:
        return self.client.get_latest_price(symbol)

    def get_candles(self, symbol: str, interval: str = "15m", limit: int = 100) -> list[dict]:
        return self.client.get_candles(symbol, interval, limit)


def validate_symbol(symbol: str) -> str:
    normalized = symbol.upper().strip()
    if normalized not in SUPPORTED_SYMBOLS:
        raise ValueError(f"Unsupported symbol: {normalized}")
    return normalized


def get_supported_symbols() -> set[str]:
    if current_app.config["MARKET_DATA_PROVIDER"] == "bitunix":
        return set(SUPPORTED_BITUNIX_SYMBOLS)
    return set(SUPPORTED_SYMBOLS)


def validate_provider_symbol(symbol: str) -> str:
    normalized = validate_symbol(symbol)
    if normalized not in get_supported_symbols():
        provider = current_app.config["MARKET_DATA_PROVIDER"]
        supported = ", ".join(sorted(get_supported_symbols()))
        raise ValueError(f"{normalized} is not supported by {provider}. Supported symbols: {supported}")
    return normalized


def get_market_data_provider() -> MarketDataProvider:
    provider_name = current_app.config["MARKET_DATA_PROVIDER"]
    if provider_name == "mock":
        return MockMarketDataProvider()
    if provider_name == "bitunix":
        return BitunixMarketDataProvider()
    raise RuntimeError(f"Unknown market data provider: {provider_name}")


def get_latest_price(symbol: str) -> float:
    return get_market_data_provider().get_latest_price(symbol)


def get_candles(symbol: str, interval: str = "15m", limit: int = 100) -> list[dict]:
    return get_market_data_provider().get_candles(symbol, interval, limit)
