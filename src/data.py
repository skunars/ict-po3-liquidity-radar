import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

BASE_URL = "https://data-api.binance.vision"
DATA_DIR = Path("data")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_json(path: str, params: dict[str, Any] | None = None) -> Any:
    response = requests.get(BASE_URL + path, params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def liquid_symbols(limit: int) -> list[str]:
    info = get_json("/api/v3/exchangeInfo")
    tickers = get_json("/api/v3/ticker/24hr")
    allowed = {
        s["symbol"] for s in info["symbols"]
        if s.get("status") == "TRADING"
        and s.get("quoteAsset") == "USDT"
        and s.get("isSpotTradingAllowed", True)
    }
    ranked = sorted(
        (t for t in tickers if t["symbol"] in allowed),
        key=lambda x: float(x.get("quoteVolume", 0) or 0),
        reverse=True,
    )
    return [t["symbol"] for t in ranked[:limit]]


def _interval(value: str) -> str:
    mapping = {"1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m", "30m": "30m", "1h": "1h", "2h": "2h", "4h": "4h", "6h": "6h", "12h": "12h"}
    if value not in mapping:
        raise ValueError(f"Unsupported Binance interval: {value}")
    return mapping[value]


def klines(symbol: str, interval: str, limit: int) -> list[dict[str, Any]]:
    rows = get_json("/api/v3/klines", {"symbol": symbol, "interval": _interval(interval), "limit": min(limit, 1000)})
    fields = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume", "trades"]
    return [dict(zip(fields, row[:len(fields)])) for row in rows]


def append_jsonl(filename: str, row: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with (DATA_DIR / filename).open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def write_json(filename: str, payload: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = DATA_DIR / (filename + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, DATA_DIR / filename)
