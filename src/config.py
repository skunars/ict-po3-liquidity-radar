from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    interval: str = "15m"
    htf_interval: str = "1h"
    lookback: int = 160
    htf_lookback: int = 120
    max_symbols: int = 30
    min_quote_volume_usd: float = 50_000_000.0
    swing_left: int = 2
    swing_right: int = 2
    liquidity_tolerance_pct: float = 0.0008
    sweep_buffer_pct: float = 0.0005
    killzone_london_start_utc: int = 7
    killzone_london_end_utc: int = 10
    killzone_newyork_start_utc: int = 13
    killzone_newyork_end_utc: int = 16
    paper_horizon_bars: int = 32
    rr_target: float = 2.0
    risk_fraction: float = 0.01


CONFIG = Config()
