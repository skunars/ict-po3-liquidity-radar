from src.strategy import htf_bias, killzone, nearest_equal_level, po3_state


def candle(o, h, l, c, t=0):
    return {"open": o, "high": h, "low": l, "close": c, "open_time": t}


def test_htf_bias_bullish():
    rows = [candle(100, 101, 99, 100 + i * 0.5) for i in range(60)]
    assert htf_bias(rows) == "Bullish"


def test_killzones():
    assert killzone(8 * 3600 * 1000) == "London"
    assert killzone(14 * 3600 * 1000) == "NewYork"
    assert killzone(20 * 3600 * 1000) is None


def test_equal_level_detection():
    level, distance = nearest_equal_level([100, 100.04, 105], 101, 0.001)
    assert level == 100.02
    assert distance > 0


def test_po3_needs_enough_data():
    assert po3_state([candle(1, 2, 0, 1)] * 10) == "Unknown"
