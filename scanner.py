import json
from datetime import datetime, timezone
from pathlib import Path

from src.config import CONFIG
from src.data import append_jsonl, klines, liquid_symbols, utc_now, write_json
from src.strategy import detect_setup

DATA = Path("data")


def read_jsonl(name: str) -> list[dict]:
    path = DATA / name
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def evaluate_open_trades() -> int:
    trades = read_jsonl("paper_trades.jsonl")
    closed = read_jsonl("closed_trades.jsonl")
    closed_ids = {x.get("trade_id") for x in closed}
    added = 0
    for trade in trades:
        tid = trade.get("trade_id")
        if not tid or tid in closed_ids:
            continue
        try:
            rows = klines(trade["symbol"], CONFIG.interval, CONFIG.lookback)
        except Exception:
            continue
        entry = float(trade["entry"])
        stop = float(trade["stop"])
        target = float(trade["target"])
        side = trade["side"]
        highs = [float(r["high"]) for r in rows]
        lows = [float(r["low"]) for r in rows]
        hit_stop = min(lows[-CONFIG.paper_horizon_bars:]) <= stop if side == "LONG" else max(highs[-CONFIG.paper_horizon_bars:]) >= stop
        hit_target = max(highs[-CONFIG.paper_horizon_bars:]) >= target if side == "LONG" else min(lows[-CONFIG.paper_horizon_bars:]) <= target
        result = None
        exit_price = None
        reason = None
        if hit_stop and hit_target:
            # Conservative intrabar ordering: stop is counted first when both are touched.
            result, exit_price, reason = "LOSS", stop, "STOP_FIRST"
        elif hit_target:
            result, exit_price, reason = "WIN", target, "TARGET"
        elif hit_stop:
            result, exit_price, reason = "LOSS", stop, "STOP"
        else:
            continue
        risk = abs(entry - stop)
        pnl_r = ((exit_price - entry) / risk) if side == "LONG" else ((entry - exit_price) / risk)
        append_jsonl("closed_trades.jsonl", {**trade, "closed_at": utc_now(), "exit": exit_price, "result": result, "exit_reason": reason, "r_multiple": round(pnl_r, 4)})
        added += 1
    return added


def main() -> None:
    DATA.mkdir(exist_ok=True)
    existing = read_jsonl("signals.jsonl")
    signal_keys = {x.get("signal_key") for x in existing}
    symbols = liquid_symbols(CONFIG.max_symbols)
    detected = 0
    closed = evaluate_open_trades()

    for symbol in symbols:
        try:
            rows = klines(symbol, CONFIG.interval, CONFIG.lookback)
            htf = klines(symbol, CONFIG.htf_interval, CONFIG.htf_lookback)
            setup = detect_setup(rows, htf, CONFIG.liquidity_tolerance_pct)
        except Exception as exc:
            append_jsonl("market_errors.jsonl", {"timestamp": utc_now(), "symbol": symbol, "error": str(exc)})
            continue
        if not setup:
            continue
        candle_time = int(rows[-1]["open_time"])
        key = f"{symbol}:{candle_time}:{setup.side}"
        if key in signal_keys:
            continue
        signal = {
            "signal_key": key,
            "timestamp": utc_now(),
            "symbol": symbol,
            "side": setup.side,
            "session": setup.session,
            "htf_bias": setup.bias,
            "po3_state": setup.po3,
            "liquidity": setup.liquidity,
            "sweep_depth": setup.sweep,
            "mss": setup.mss,
            "displacement": setup.displacement,
            "fvg": setup.fvg,
            "entry": setup.entry,
            "stop": setup.stop,
            "target": setup.target,
            "reason": setup.reason,
            "status": "PAPER_OPEN",
        }
        append_jsonl("signals.jsonl", signal)
        append_jsonl("paper_trades.jsonl", {**signal, "trade_id": key})
        signal_keys.add(key)
        detected += 1

    open_trades = len(read_jsonl("paper_trades.jsonl")) - len(read_jsonl("closed_trades.jsonl"))
    write_json("daily_report.json", {"updated_at": utc_now(), "symbols_scanned": len(symbols), "new_signals": detected, "closed_trades_this_run": closed, "paper_open_estimate": max(open_trades, 0)})
    print(f"ICT_PO3_V1 | symbols={len(symbols)} new_signals={detected} closed={closed}")


if __name__ == "__main__":
    main()
