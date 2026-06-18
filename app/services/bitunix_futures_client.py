from __future__ import annotations

import hashlib
import json
import secrets
import time
from urllib.parse import urlencode

import requests


SUPPORTED_BITUNIX_SYMBOLS = {"BTCUSDT", "ETHUSDT", "SOLUSDT"}


class BitunixAPIError(RuntimeError):
    pass


class BitunixFuturesClient:
    def __init__(self, base_url: str, api_key: str | None = None, api_secret: str | None = None, timeout: int = 12):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.api_secret = api_secret
        self.timeout = timeout

    def _request(self, method: str, path: str, params: dict | None = None, payload: dict | None = None, private: bool = False) -> dict:
        params = params or {}
        payload = payload or {}
        headers = {"Content-Type": "application/json"}
        body = json.dumps(payload, separators=(",", ":")) if payload else ""
        if private:
            if not self.api_key or not self.api_secret:
                raise BitunixAPIError("Bitunix API credentials are not configured")
            nonce = secrets.token_hex(16)
            timestamp = str(int(time.time() * 1000))
            query = "".join(f"{key}{params[key]}" for key in sorted(params))
            digest = hashlib.sha256(f"{nonce}{timestamp}{self.api_key}{query}{body}".encode()).hexdigest()
            signature = hashlib.sha256(f"{digest}{self.api_secret}".encode()).hexdigest()
            headers.update({"api-key": self.api_key, "nonce": nonce, "timestamp": timestamp, "sign": signature})
        try:
            response = requests.request(method, f"{self.base_url}{path}", params=params or None, data=body or None, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise BitunixAPIError(f"Bitunix request failed: {exc}") from exc
        if not isinstance(result, dict) or str(result.get("code", "0")) not in {"0", "200"}:
            raise BitunixAPIError(f"Bitunix rejected request: {result.get('msg') or result.get('message') or 'unknown response'}")
        return result

    @staticmethod
    def _symbol(symbol: str) -> str:
        value = symbol.upper().strip()
        if value not in SUPPORTED_BITUNIX_SYMBOLS:
            raise ValueError(f"Unsupported Bitunix symbol: {value}")
        return value

    def get_futures_symbols(self) -> list[dict]:
        data = self._request("GET", "/api/v1/futures/market/trading_pairs").get("data", [])
        return [item for item in data if item.get("symbol") in SUPPORTED_BITUNIX_SYMBOLS]

    def get_latest_price(self, symbol: str) -> float:
        data = self._request("GET", "/api/v1/futures/market/tickers", {"symbols": self._symbol(symbol)}).get("data", [])
        if not data:
            raise BitunixAPIError("Bitunix returned no ticker data")
        price = data[0].get("lastPrice") or data[0].get("markPrice")
        if price is None:
            raise BitunixAPIError("Bitunix ticker response has no price")
        return float(price)

    def get_candles(self, symbol: str, interval: str = "15m", limit: int = 200) -> list[dict]:
        if interval not in {"1m", "5m", "15m", "30m", "1h", "4h", "1d"}:
            raise ValueError("Unsupported Bitunix candle interval")
        if not 1 <= limit <= 200:
            raise ValueError("Bitunix candle limit must be between 1 and 200")
        data = self._request("GET", "/api/v1/futures/market/kline", {"symbol": self._symbol(symbol), "interval": interval, "limit": limit}).get("data", [])
        candles = [{"open": float(x["open"]), "high": float(x["high"]), "low": float(x["low"]), "close": float(x["close"]), "volume": float(x.get("baseVol") or x.get("volume") or 0), "timestamp": int(x["time"])} for x in data]
        candles.sort(key=lambda item: item["timestamp"])
        if not candles:
            raise BitunixAPIError("Bitunix returned no candle data")
        return candles

    def get_order_book(self, symbol: str, depth: int = 20) -> dict:
        allowed = (1, 5, 15, 50)
        api_depth = next((value for value in allowed if value >= depth), 50)
        return self._request("GET", "/api/v1/futures/market/depth", {"symbol": self._symbol(symbol), "limit": api_depth}).get("data", {})

    def get_funding_rate(self, symbol: str) -> dict:
        return self._request("GET", "/api/v1/futures/market/funding_rate", {"symbol": self._symbol(symbol)}).get("data", {})

    def get_account(self, margin_coin: str = "USDT") -> dict:
        return self._request("GET", "/api/v1/futures/account", {"marginCoin": margin_coin}, private=True).get("data", {})

    def get_positions(self, symbol: str | None = None) -> list[dict]:
        params = {"symbol": self._symbol(symbol)} if symbol else {}
        data = self._request("GET", "/api/v1/futures/position/get_pending_positions", params, private=True).get("data", [])
        return data if isinstance(data, list) else data.get("positionList", [])

    def place_order(self, payload: dict) -> dict:
        return self._request("POST", "/api/v1/futures/trade/place_order", payload=payload, private=True)

    def get_order_detail(self, order_id: str) -> dict:
        return self._request("GET", "/api/v1/futures/trade/get_order_detail", {"orderId": order_id}, private=True)

    def cancel_all_orders(self, symbol: str) -> dict:
        return self._request("POST", "/api/v1/futures/trade/cancel_all_orders", payload={"symbol": self._symbol(symbol)}, private=True)
