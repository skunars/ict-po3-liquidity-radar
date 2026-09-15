# ICT PO3 Liquidity Radar

Independent research and paper-trading system for testing a measurable combination of:

- HTF bias
- PO3 session structure (Accumulation → Manipulation → Distribution)
- EQH/EQL liquidity
- ICT-style London/New York killzones
- Liquidity sweeps
- Market-structure shift (MSS)
- Displacement and FVG context

## V1 principles

- Paper trading only. No exchange orders.
- No scoring in the baseline version.
- No MOST, VWAP or KripNet in V1; those are separate future experiments.
- Every detected setup is logged with its full context so later results can be tested statistically.
- GitHub Actions runs every 15 minutes; the local PC does not need to be on.
- The system should collect a meaningful sample before strategy rules are changed.

## Data

The workflow persists JSONL files under `data/`:

- `market_snapshots.jsonl`
- `signals.jsonl`
- `paper_trades.jsonl`
- `closed_trades.jsonl`
- `daily_report.json`

## Initial market universe

V1 uses liquid Binance USDT perpetual symbols discovered from the public exchange API. The scanner is deliberately limited to a manageable set of liquid markets rather than trying to scan every contract.

## Important

This repository is intentionally independent from the other trading, pre-listing, pump and sports projects. Do not mix their data, state files or strategy rules with this project.
