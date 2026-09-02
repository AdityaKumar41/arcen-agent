#!/usr/bin/env python3
"""chart_analyzer.py - Automated chart & market context analyzer.

Pulls recent OHLCV (Binance public for crypto, Yahoo for stocks/forex),
computes technical indicators (RSI, MACD, EMA/SMA, Bollinger, ATR, volume
trend), derives support/resistance and swing structure, and emits a structured
"market context" JSON the agent can turn into a narrative.

Zero external dependencies (stdlib only).  Read-only.
"""

import argparse
import json
import math
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import time
from typing import Any, Dict, List, Optional, Sequence

BINANCE_BASE = os.getenv("BINANCE_API_URL", "https://api.binance.com/api/v3")
YAHOO_BASE = "https://query1.finance.yahoo.com"
YAHOO_BASE2 = "https://query2.finance.yahoo.com"
UA = "Mozilla/5.0 (compatible; arcen-chart-analyzer/1.0)"
BINANCE_IV = {"15m", "1h", "4h", "1d", "1w"}


def _get(url: str, timeout: int = 25, retries: int = 3) -> Any:
    delay = 1.0
    last: Exception = RuntimeError("no attempts")
    for _ in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                       "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode()
                return json.loads(body) if body else None
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            last = e
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"HTTP failed: {last}")


def fetch_candles(symbol: str, source: str, interval: str, limit: int = 200) -> List[Dict[str, Any]]:
    if source == "binance":
        iv = interval if interval in BINANCE_IV else "1d"
        qs = urllib.parse.urlencode({"symbol": symbol.upper(), "interval": iv,
                                     "limit": str(limit)})
        rows = _get(f"{BINANCE_BASE}/klines?{qs}")
        if isinstance(rows, dict) and "code" in rows:
            raise RuntimeError(f"Binance error: {rows}")
        return [{"timestamp": int(r[0]), "open": float(r[1]), "high": float(r[2]),
                 "low": float(r[3]), "close": float(r[4]), "volume": float(r[5])}
                for r in rows or []]
    # yahoo
    ymap = {"1d": "1d", "4h": "1d", "1h": "60m", "15m": "15m", "1w": "1wk"}
    iv = ymap.get(interval, "1d")
    qs = urllib.parse.urlencode({"interval": iv, "range": "1y" if iv == "1d" else "3mo"})
    data = _get(f"{YAHOO_BASE}/v8/finance/chart/{urllib.parse.quote(symbol)}?{qs}")
    if data is None:
        data = _get(f"{YAHOO_BASE2}/v8/finance/chart/{urllib.parse.quote(symbol)}?{qs}")
    result = (data or {}).get("chart", {}).get("result") or []
    if not result:
        raise RuntimeError(f"No data for {symbol}")
    ts = result[0].get("timestamp") or []
    q = (result[0].get("indicators", {}).get("quote") or [{}])[0]
    rows = []
    for i, t in enumerate(ts):
        c = q.get("close", [None] * len(ts))
        if c[i] is None:
            continue
        rows.append({"timestamp": int(t) * 1000,
                     "open": q.get("open", c)[i] or c[i],
                     "high": q.get("high", c)[i] or c[i],
                     "low": q.get("low", c)[i] or c[i],
                     "close": float(c[i]),
                     "volume": float(q.get("volume", [0] * len(ts))[i] or 0)})
    return rows[-limit:]


# --- indicators (embedded; matches backtester.fn conventions) ---

def _sma(v: Sequence[float], n: int) -> List[Optional[float]]:
    out: List[Optional[float]] = [None] * len(v)
    acc = 0.0
    for i, x in enumerate(v):
        acc += x
        if i >= n:
            acc -= v[i - n]
        if i >= n - 1:
            out[i] = acc / n
    return out


def _ema(v: Sequence[float], n: int) -> List[Optional[float]]:
    out: List[Optional[float]] = [None] * len(v)
    if not v:
        return out
    k = 2.0 / (n + 1)
    prev = v[0]
    out[0] = prev
    for i in range(1, len(v)):
        prev = v[i] * k + prev * (1 - k)
        out[i] = prev
    return out


def _rsi(v: Sequence[float], n: int = 14) -> List[Optional[float]]:
    out: List[Optional[float]] = [None] * len(v)
    if len(v) <= n:
        return out
    g = l = 0.0
    for i in range(1, n + 1):
        c = v[i] - v[i - 1]
        g += max(c, 0.0)
        l += max(-c, 0.0)
    ag, al = g / n, l / n
    out[n] = 100.0 if al == 0 else 100.0 - 100.0 / (1.0 + ag / al)
    for i in range(n + 1, len(v)):
        c = v[i] - v[i - 1]
        ag = (ag * (n - 1) + max(c, 0.0)) / n
        al = (al * (n - 1) + max(-c, 0.0)) / n
        out[i] = 100.0 if al == 0 else 100.0 - 100.0 / (1.0 + ag / al)
    return out


def _atr(h: Sequence[float], l: Sequence[float], c: Sequence[float], n: int = 14) -> List[Optional[float]]:
    trs = []
    for i in range(len(c)):
        if i == 0:
            trs.append(h[i] - l[i])
        else:
            trs.append(max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1])))
    out: List[Optional[float]] = [None] * len(c)
    for i in range(n - 1, len(trs)):
        out[i] = sum(trs[i - n + 1: i + 1]) / n
    return out


def _boll(v: Sequence[float], n: int = 20, mult: float = 2.0):
    mid = _sma(v, n)
    up: List[Optional[float]] = [None] * len(v)
    lo: List[Optional[float]] = [None] * len(v)
    for i in range(n - 1, len(v)):
        w = v[i - n + 1: i + 1]
        m = sum(w) / n
        sd = math.sqrt(sum((x - m) ** 2 for x in w) / n)
        up[i], lo[i] = m + mult * sd, m - mult * sd
    return up, mid, lo


def _macd(v: Sequence[float]):
    ef = _ema(v, 12)
    es = _ema(v, 26)
    line = [a - b if a is not None and b is not None else None for a, b in zip(ef, es)]
    sig_in = [x if x is not None else 0.0 for x in line]
    sig = _ema(sig_in, 9)
    hist = [a - b if a is not None and b is not None else None for a, b in zip(line, sig)]
    return line, sig, hist


# --- analysis ---

def _support_resistance(rows: List[Dict[str, Any]], window: int = 60) -> Dict[str, Any]:
    """Swing low -> support, swing high -> resistance over a trailing window."""
    highs = [r["high"] for r in rows[-window:]]
    lows = [r["low"] for r in rows[-window:]]
    window_len = min(5, max(3, len(highs) // 12))  # local swing neighbourhood
    swings_high: List[float] = []
    swings_low: List[float] = []
    for i in range(window_len, len(highs) - window_len):
        hb = highs[i - window_len:i + window_len + 1]
        lb = lows[i - window_len:i + window_len + 1]
        if highs[i] == max(hb):
            swings_high.append(highs[i])
        if lows[i] == min(lb):
            swings_low.append(lows[i])
    level = lambda xs: round(sum(xs) / len(xs), 4) if xs else None
    return {
        "resistance": level(swings_high[-3:]),
        "recent_swing_highs": [round(x, 4) for x in swings_high[-5:]],
        "support": level(swings_low[-3:]),
        "recent_swing_lows": [round(x, 4) for x in swings_low[-5:]],
    }


def _segment_rsi(value: Optional[float]) -> str:
    if value is None:
        return "unknown"
    if value >= 70:
        return "overbought"
    if value <= 30:
        return "oversold"
    if value >= 55:
        return "strong"
    if value <= 45:
        return "weak"
    return "neutral"


def _trend_label(close50: Optional[float], close200: Optional[float],
                 ema20, close) -> str:
    if close200 is not None and close50 is not None:
        if close50 > close200 and ema20 is not None and close > ema20:
            return "bullish"
        if close50 < close200 and ema20 is not None and close < ema20:
            return "bearish"
    if ema20 is not None:
        return "bullish" if close > ema20 else "bearish"
    return "neutral"


def analyze(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if len(rows) < 50:
        raise RuntimeError(f"Need >=50 candles, got {len(rows)}")
    closes = [r["close"] for r in rows]
    highs = [r["high"] for r in rows]
    lows = [r["low"] for r in rows]
    vols = [r["volume"] for r in rows]
    last = closes[-1]

    r = _rsi(closes)
    macd_line, macd_sig, macd_hist = _macd(closes)
    up, mid, lo = _boll(closes)
    at = _atr(highs, lows, closes)
    e20 = _ema(closes, 20)
    s50 = _sma(closes, 50)
    s200 = _sma(closes, 200)
    sr = _support_resistance(rows)

    rsi_now = r[-1]
    vol_avg = sum(vols[-20:]) / 20 if vols else 0
    vol_now = vols[-1] if vols else 0
    band_position = None
    if up[-1] is not None and lo[-1] is not None and up[-1] != lo[-1]:
        band_position = round((last - lo[-1]) / (up[-1] - lo[-1]) * 100, 1)

    change_24h_pct = None
    for i in range(len(closes) - 1, 0, -1):
        if rows[i]["timestamp"] - rows[i - 1]["timestamp"] >= 86_400_000:
            change_24h_pct = round((last / closes[i - 1] - 1) * 100, 2)
            break

    return {
        "symbol": None,
        "timestamp": rows[-1]["timestamp"],
        "bar_count": len(rows),
        "last_close": last,
        "change_24h_pct": change_24h_pct,
        "trend": _trend_label(s50[-1], s200[-1], e20[-1], last),
        "indicators": {
            "rsi14": {"value": round(rsi_now, 2), "zone": _segment_rsi(rsi_now)}
            if rsi_now is not None else None,
            "macd": {"line": round(macd_line[-1], 6) if macd_line[-1] is not None else None,
                     "signal": round(macd_sig[-1], 6) if macd_sig[-1] is not None else None,
                     "histogram": round(macd_hist[-1], 6) if macd_hist[-1] is not None else None,
                     "cross": _macd_cross(macd_line, macd_sig)},
            "sma50": round(s50[-1], 4) if s50[-1] is not None else None,
            "sma200": round(s200[-1], 4) if s200[-1] is not None else None,
            "ema20": round(e20[-1], 4) if e20[-1] is not None else None,
            "bollinger": {
                "upper": round(up[-1], 4) if up[-1] is not None else None,
                "mid": round(mid[-1], 4) if mid[-1] is not None else None,
                "lower": round(lo[-1], 4) if lo[-1] is not None else None,
                "position_pct": band_position,
            },
            "atr14": round(at[-1], 4) if at[-1] is not None else None,
        },
        "support_resistance": sr,
        "volume": {
            "current": vol_now,
            "avg_20": round(vol_avg, 2),
            "ratio": round(vol_now / vol_avg, 2) if vol_avg else None,
        },
        "summary": _summary_blob(last, rsi_now, macd_line[-1], macd_sig[-1],
                                 s50[-1], s200[-1], sr, band_position),
    }


def _macd_cross(line, sig) -> str:
    for i in range(len(line) - 1, 0, -1):
        if line[i] is None or sig[i] is None or line[i - 1] is None or sig[i - 1] is None:
            continue
        if line[i - 1] <= sig[i - 1] and line[i] > sig[i]:
            return "bullish_cross"
        if line[i - 1] >= sig[i - 1] and line[i] < sig[i]:
            return "bearish_cross"
    return "none"


def _summary_blob(price, rsi, mline, msig, s50, s200, sr, band) -> str:
    parts = [f"Price {price:,.2f}."]
    if rsi is not None:
        parts.append(f"RSI14 {rsi:.1f} ({_segment_rsi(rsi)}).")
    if mline is not None and msig is not None:
        parts.append(f"MACD {'above' if mline > msig else 'below'} signal.")
    if s50 is not None and s200 is not None:
        parts.append(f"SMA50 {'above' if s50 > s200 else 'below'} SMA200.")
    if sr.get("support") is not None and sr.get("resistance") is not None:
        parts.append(f"Support ~{sr['support']:,.0f}, resistance ~{sr['resistance']:,.0f}.")
    if band is not None:
        parts.append(f"Bollinger band position {band:.0f}% (0=lower, 100=upper).")
    return " ".join(parts)


def cmd_chart(args: argparse.Namespace) -> None:
    rows = fetch_candles(args.symbol, args.source, args.interval, args.limit)
    ctx = analyze(rows)
    ctx["symbol"] = args.symbol
    ctx["source"] = args.source
    ctx["interval"] = args.interval
    if args.json:
        print(json.dumps(ctx, indent=2, default=str))
        return
    print(f"{args.symbol} ({args.source} {args.interval}) — {ctx['timestamp']}")
    print(f"  trend      : {ctx['trend']}")
    print(f"  last close : {ctx['last_close']:,.2f}  24h: {ctx['change_24h_pct']}" if ctx['change_24h_pct'] is not None
          else f"  last close : {ctx['last_close']:,.2f}")
    ind = ctx["indicators"]
    if ind["rsi14"]:
        print(f"  RSI14      : {ind['rsi14']['value']} ({ind['rsi14']['zone']})")
    if ind["macd"]["line"] is not None:
        print(f"  MACD       : line {ind['macd']['line']} signal {ind['macd']['signal']} ({ind['macd']['cross']})")
    if ind["sma50"] is not None:
        print(f"  SMA        : 50={ind['sma50']:,.2f} 200={ind['sma200']:,.2f}")
    if ind["bollinger"]["upper"] is not None:
        print(f"  Bollinger  : U={ind['bollinger']['upper']:,.2f} pos={ind['bollinger']['position_pct']}%")
    if ind["atr14"] is not None:
        print(f"  ATR14      : {ind['atr14']:.4f} ({ind['atr14']/ctx['last_close']*100:.2f}% of price)")
    sr = ctx["support_resistance"]
    print(f"  Support    : {sr['support']}   Resistance: {sr['resistance']}")
    v = ctx["volume"]
    print(f"  Volume     : ratio {v['ratio']} vs 20-bar avg")
    print(f"  Summary    : {ctx['summary']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chart_analyzer",
        description="Automated chart & market context analyzer (crypto/stocks/forex).",
    )
    parser.add_argument("symbol", help="e.g. BTCUSDT, EURUSD=X, AAPL")
    parser.add_argument("--source", default="binance", choices=["binance", "yahoo"])
    parser.add_argument("--interval", default="1d", choices=["15m", "1h", "4h", "1d", "1w"])
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        cmd_chart(args)
    except KeyboardInterrupt:
        print(json.dumps({"error": "Interrupted by user"}))
        return 130
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())