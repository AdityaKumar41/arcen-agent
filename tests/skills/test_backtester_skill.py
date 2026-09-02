from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "optional-skills"
    / "trading"
    / "backtester"
    / "scripts"
    / "backtester.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("backtester_skill", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _rows(drift=0.5, n=220):
    prices = [100 + i * drift + (0 if (i % 7) else -8) for i in range(n)]
    return [
        {"timestamp": 1700000000000 + i, "open": p, "high": p + 2, "low": p - 2,
         "close": p, "volume": 100.0}
        for i, p in enumerate(prices)
    ]


def test_rsi_ranges_and_reaches_extremes():
    mod = load_module()
    # monotonic rise -> RSI should trend toward 100
    rising = [100 + i for i in range(40)]
    r = mod.rsi(rising, 14)
    assert r[-1] == 100.0
    # monotonic fall -> RSI 0
    falling = [200 - i for i in range(40)]
    assert mod.rsi(falling, 14)[-1] == 0.0


def test_sma_matches_simple_average():
    mod = load_module()
    v = [1.0, 2.0, 3.0, 4.0, 5.0]
    s = mod.sma(v, 3)
    assert s[2] == 2.0
    assert s[3] == 3.0
    assert s[4] == 4.0
    assert s[0] is None


def test_ema_first_value_is_seed():
    mod = load_module()
    v = [5.0, 6.0, 7.0, 8.0]
    e = mod.ema(v, 3)
    assert e[0] == 5.0
    assert e[-1] > e[0]


def test_bollinger_band_ordering():
    mod = load_module()
    v = [10 + (i % 5) for i in range(40)]
    up, mid, low = mod.bollinger(v, 20, 2.0)
    assert up[-1] > mid[-1] > low[-1]
    assert up[-1] is not None


def test_macd_histogram_shape():
    mod = load_module()
    v = [float(i) for i in range(60)]
    line, sig, hist = mod.macd(v, 12, 26, 9)
    assert line[-1] > 0
    assert abs(hist[-1] - (line[-1] - sig[-1])) < 1e-9
    assert mod.macd([], 12, 26, 9)[0] == []


def test_all_strategies_return_signal_series():
    mod = load_module()
    closes = [120 + i * 0.3 for i in range(120)]
    for name in mod.STRATEGIES:
        sigs = mod.strategy_signals(name, closes)
        assert len(sigs) == len(closes)
        assert set(sigs) <= {"flat", "long", "short"}


def test_strategy_signals_unknown_name():
    mod = load_module()
    try:
        mod.strategy_signals("nope", [1, 2, 3])
    except ValueError as e:
        assert "Unknown strategy" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_run_backtest_groups_and_gains():
    mod = load_module()
    rows = _rows()
    res = mod.run_backtest(rows, "sma_cross", initial=10000, fee=0.1)
    assert res["bars"] == len(rows)
    assert res["initial_capital"] == 10000
    assert isinstance(res["total_return_pct"], (int, float))
    assert isinstance(res["max_drawdown_pct"], (int, float))


def test_max_drawdown_negative_on_dip():
    mod = load_module()
    assert mod._max_drawdown([100, 110, 90, 95]) < 0


def test_price_parser_iso_and_ms():
    mod = load_module()
    assert mod._parse_ts("2024-01-01") > 0
    assert mod._parse_ts("1700000000000") == 1700000000000


def test_csv_export_writes_header():
    mod = load_module()
    import tempfile, os
    tmp = tempfile.mktemp(suffix=".csv")
    try:
        mod._write_csv(_rows(2), tmp)
        with open(tmp) as fh:
            header = fh.readline().strip()
        assert header == "timestamp,open,high,low,close,volume"
    finally:
        os.unlink(tmp)