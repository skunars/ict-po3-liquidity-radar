from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class Setup:
    side: str
    session: str
    bias: str
    po3: str
    liquidity: str
    sweep: float
    mss: bool
    displacement: bool
    fvg: bool
    entry: float
    stop: float
    target: float
    reason: str


def closes(rows: list[dict[str, Any]]) -> list[float]:
    return [float(r["close"]) for r in rows]


def htf_bias(rows: list[dict[str, Any]]) -> str:
    c = closes(rows)
    if len(c) < 50:
        return "Neutral"
    fast = sum(c[-20:]) / 20
    slow = sum(c[-50:]) / 50
    if fast > slow and c[-1] > c[-10]:
        return "Bullish"
    if fast < slow and c[-1] < c[-10]:
        return "Bearish"
    return "Neutral"


def killzone(open_time_ms: int) -> str | None:
    hour = datetime.fromtimestamp(open_time_ms / 1000, tz=timezone.utc).hour
    if 7 <= hour < 10:
        return "London"
    if 13 <= hour < 16:
        return "NewYork"
    return None


def swings(rows: list[dict[str, Any]], left: int = 2, right: int = 2) -> tuple[list[float], list[float]]:
    highs, lows = [], []
    hs = [float(r["high"]) for r in rows]
    ls = [float(r["low"]) for r in rows]
    for i in range(left, len(rows) - right):
        if hs[i] == max(hs[i-left:i+right+1]):
            highs.append(hs[i])
        if ls[i] == min(ls[i-left:i+right+1]):
            lows.append(ls[i])
    return highs, lows


def nearest_equal_level(levels: list[float], price: float, tolerance: float) -> tuple[float | None, float]:
    if len(levels) < 2:
        return None, 0.0
    for i in range(len(levels) - 1, 0, -1):
        a, b = levels[i], levels[i - 1]
        if abs(a - b) / max(b, 1e-12) <= tolerance:
            level = (a + b) / 2
            return level, abs(price - level) / max(level, 1e-12)
    return None, 0.0


def po3_state(rows: list[dict[str, Any]]) -> str:
    if len(rows) < 24:
        return "Unknown"
    recent = rows[-24:]
    ranges = [float(r["high"]) - float(r["low"]) for r in recent]
    early = recent[:8]
    mid = recent[8:16]
    late = recent[16:]
    early_range = max(float(r["high"]) for r in early) - min(float(r["low"]) for r in early)
    mid_high = max(float(r["high"]) for r in mid)
    mid_low = min(float(r["low"]) for r in mid)
    late_move = float(late[-1]["close"]) - float(late[0]["open"])
    typical = sum(ranges) / len(ranges)
    if early_range <= typical * 5 and (mid_high - mid_low) >= early_range * 0.8:
        if abs(late_move) >= typical * 2:
            return "Distribution"
        return "Manipulation"
    return "Accumulation"


def detect_setup(rows: list[dict[str, Any]], htf_rows: list[dict[str, Any]], tolerance: float = 0.0008) -> Setup | None:
    if len(rows) < 30 or len(htf_rows) < 50:
        return None
    current = rows[-1]
    session = killzone(int(current["open_time"]))
    if not session:
        return None
    bias = htf_bias(htf_rows)
    if bias == "Neutral":
        return None
    highs, lows = swings(rows)
    price = float(current["close"])
    eqh, _ = nearest_equal_level(highs, price, tolerance)
    eql, _ = nearest_equal_level(lows, price, tolerance)
    prev = rows[-2]
    prev_close = float(prev["close"])
    high = float(current["high"])
    low = float(current["low"])
    close = price
    candle_range = max(high - low, 1e-12)
    body = abs(close - float(current["open"]))
    displacement = body / candle_range >= 0.65
    mss = False
    fvg = False

    if bias == "Bullish" and eql is not None:
        swept = low < eql * (1 - 0.0005) and close > eql
        mss = close > float(rows[-3]["high"])
        if swept and mss and displacement:
            fvg = low > float(rows[-2]["high"])
            entry = close
            stop = min(low, eql * (1 - 0.001))
            risk = entry - stop
            if risk <= 0:
                return None
            target = entry + risk * 2
            return Setup("LONG", session, bias, po3_state(rows), "EQL", (eql-low)/eql, mss, displacement, fvg, entry, stop, target, "EQL sweep + bullish MSS + displacement")

    if bias == "Bearish" and eqh is not None:
        swept = high > eqh * (1 + 0.0005) and close < eqh
        mss = close < float(rows[-3]["low"])
        if swept and mss and displacement:
            fvg = high < float(rows[-2]["low"])
            entry = close
            stop = max(high, eqh * (1 + 0.001))
            risk = stop - entry
            if risk <= 0:
                return None
            target = entry - risk * 2
            return Setup("SHORT", session, bias, po3_state(rows), "EQH", (high-eqh)/eqh, mss, displacement, fvg, entry, stop, target, "EQH sweep + bearish MSS + displacement")
    return None
