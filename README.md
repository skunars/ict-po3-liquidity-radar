# ICT PO3 Liquidity Radar

Research and paper-trading system for PO3 + ICT killzones + EQH/EQL liquidity sweeps.

- Paper trading only; no live orders.
- Runs automatically every 15 minutes via GitHub Actions.
- Market data source: Binance public spot market-data mirror (`data-api.binance.vision`), chosen because GitHub-hosted runners are geo-blocked from Binance USD-M futures REST endpoints.
- 15m execution timeframe with 1h higher-timeframe confirmation.
- Data is persisted under `data/` after successful runs.
