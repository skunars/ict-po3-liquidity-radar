import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

BASE_URL = "https://api.bybit.com"
DATA_DIR = Path("data")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_json(path: str, params: dict[str, Any] | None = None) -> Any:
    response = requests.get(BASE_URL + path, params=params, timeout=20)
    response.raise_for_status()
    payload = response.json()
    if payload.get("retCode") != 0:
        raise RuntimeError(f"Bybit API error: {payload.get('retCode')} {payload.get('retMsg')}")
    return payload["result"]


def liquid_symbols(limit: int) -> list[str]:
    info = get_json("/v5/market/instruments-info", {"category": "linear", "status": "Trading", "limit": 1000})
    tickers = get_json("/v5/market/tickers", {"category": "linear"})
    allowed = {
        s["symbol"] for s in info["list"]
        if s.get("status") == "Trading"
        and s.get("contractType") == "LinearPerpetual"
        and s.get("quoteCoin") == "USDT"
    }
    ranked = sorted(
        (t for t in tickers["list"] if t["symbol"] in allowed),
        key=lambda x: float(x.get("turnover24h", 0) or 0),
        reverse=True,
    )
    return [t["symbol"] for t in ranked[:limit]]


def _interval(value: str) -> str:
    mapping = {"1m": "1", "3m": "3", "5m": "5", "15m": "15", "30m": "30", "1h": "60", "2h": "120", "4h": "240", "6h": "360", "12h": "720"}
    if value not in mapping:
        raise ValueError(f"Unsupported Bybit interval: {value}")
    return mapping[value]


def klines(symbol: str, interval: str, limit: int) -> list[dict[str, Any]]:
    result = get_json("/v5/market/kline", {"category": "linear", "symbol": symbol, "interval": _interval(interval), "limit": min(limit, 1000)})
    fields = ["open_time", "open", "high", "low", "close", "volume", "quote_volume"]
    rows = [dict(zip(fields, row)) for row in result["list"]]
    return sorted(rows, key=lambda x: int(x["open_time"]))


def append_jsonl(filename: str, row: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with (DATA_DIR / filename).open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def write_json(filename: str, payload: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = DATA_DIR / (filename + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, DATA_DIR / filename)
