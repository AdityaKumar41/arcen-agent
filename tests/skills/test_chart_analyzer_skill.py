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
    / "chart-analyzer"
    / "scripts"
    / "chart_analyzer.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("chart_analyzer_skill", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _rows(n=200, base=100.0, drift=0.4):
    import math
    out = []
    for i in range(n):
        px = base + i * drift + 6 * math.sin(i / 5) + (0 if (i % 7) else -5)
        out.append({"timestamp": 1700000000000 + i * 86_400_000, "open": px,
                    "high": px + 3, "low": px - 3, "close": px, "volume": 500.0})
    return out


def test_analyze_returns_indicator_snapshot():
    mod = load_module()
    ctx = mod.analyze(_rows())
    assert ctx["bar_count"] == 200
    assert ctx["last_close"] > 0
    ind = ctx["indicators"]
    assert ind["rsi14"]["zone"] in {"overbought", "oversold", "strong", "weak", "neutral"}
    assert ind["macd"]["line"] is not None
    assert ind["bollinger"]["upper"] > ind["bollinger"]["lower"]
    assert ind["atr14"] is not None


def test_analyze_trend_label_bullish():
    mod = load_module()
    ctx = mod.analyze(_rows(base=100.0, drift=0.8))
    assert ctx["trend"] in {"bullish", "bearish", "neutral"}


def test_support_resistance_matches_swings():
    mod = load_module()
    rows = _rows()
    sr = mod._support_resistance(rows, window=60)
    assert sr["support"] is not None
    assert sr["resistance"] is not None
    assert sr["resistance"] >= sr["support"]


def test_segment_rsi_labels():
    mod = load_module()
    assert mod._segment_rsi(85) == "overbought"
    assert mod._segment_rsi(12) == "oversold"
    assert mod._segment_rsi(64) == "strong"
    assert mod._segment_rsi(48) == "neutral"
    assert mod._segment_rsi(None) == "unknown"


def test_volume_ratio():
    mod = load_module()
    ctx = mod.analyze(_rows())
    assert ctx["volume"]["ratio"] is not None


def test_analyze_rejects_short_series():
    mod = load_module()
    try:
        mod.analyze(_rows(n=10))
    except RuntimeError as e:
        assert "50 candles" in str(e)
    else:
        raise AssertionError("expected RuntimeError")


def test_main_chart_json(capsys):
    mod = load_module()
    with patch.object(mod, "fetch_candles", return_value=_rows()):
        rc = mod.main(["BTCUSDT", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["symbol"] == "BTCUSDT"
    assert out["trend"] in {"bullish", "bearish", "neutral"}