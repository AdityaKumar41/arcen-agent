#!/usr/bin/env python3
"""backtester.py - Multi-market algorithmic trading backtester.

Cross-asset OHLCV engine: crypto (Binance public REST), stocks and forex
(Yahoo Finance chart API).  Runs technical-indicator strategies over a symbol,
compares strategies, sweeps parameters, and exports equity/trade analytics.

Zero external dependencies (stdlib only).  Historical OHLCV is fetched from
free public endpoints with a small retry/backoff wrapper.

Commands:
  quit                                                     # no-op, doc-only
  fetch <symbol> --source binance|yahoo --interval 1d --start ... --out file.csv
  backtest <symbol> --strategy sma_cross|rsi_meanrev|macd|bollinger ...
  compare <symbol>                                     # rank all strategies
  optimize <symbol> --strategy sma_cross --grid ...
  download <symbol> --out bh_ohlcv.csv                 # export raw OHLCV

All commands accept --json for machine-readable output.
"""

import argparse
import csv
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Configuration / HTTP
# ---------------------------------------------------------------------------

BINANCE_BASE = os.getenv("BINANCE_API_URL", "https://api.binance.com/api/v3")
YAHOO_BASE = "https://query1.finance.yahoo.com"
YAHOO_BASE2 = "https://query2.finance.yahoo.com"
USER_AGENT = "Mozilla/5.0 (compatible; arcen-backtester/1.0)"

INTERVALS = {"1m", "5m", "15m", "1h", "4h", "1d", "1w"}
BINANCE_INTERVALS = {"1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w"}
YAHOO_MAP = {"1d": "1d", "1h": "60m", "4h": "1d", "1w": "1wk", "15m": "15m", "5m": "5m", "1m": "1m"}


def _get(url: str, timeout: int = 25, retries: int = 3) -> Any:
    delay = 1.0
    last: Exception = RuntimeError("no attempts")
    for _ in range(retries):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
            )
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
    raise RuntimeError(f"HTTP failed after {retries} attempts: {last}")


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

def fetch_binance(symbol: str, interval: str, start_ms: Optional[int],
                  end_ms: Optional[int], limit: int = 1000) -> List[Dict[str, Any]]:
    iv = interval if interval in BINANCE_INTERVALS else "1d"
    params = {"symbol": symbol.upper(), "interval": iv, "limit": str(limit)}
    if start_ms:
        params["startTime"] = str(start_ms)
    if end_ms:
        params["endTime"] = str(end_ms)
    qs = urllib.parse.urlencode(params)
    rows = _get(f"{BINANCE_BASE}/klines?{qs}")
    if isinstance(rows, dict) and "code" in rows:
        raise RuntimeError(f"Binance error: {rows}")
    out: List[Dict[str, Any]] = []
    for row in rows or []:
        out.append({
            "timestamp": int(row[0]),
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": float(row[5]),
        })
    return out


def fetch_yahoo(symbol: str, interval: str, start_ms: Optional[int],
                end_ms: Optional[int]) -> List[Dict[str, Any]]:
    iv = YAHOO_MAP.get(interval, "1d")
    params: Dict[str, str] = {"interval": iv}
    # Yahoo chart accepts range OR period1/period2 (unix seconds)
    if start_ms:
        params["period1"] = str(int(start_ms / 1000))
        params["period2"] = str(int((end_ms or int(time.time() * 1000)) / 1000))
    else:
        params["range"] = "2y" if iv == "1d" else "1y"
    qs = urllib.parse.urlencode(params)
    url = f"{YAHOO_BASE}/v8/finance/chart/{urllib.parse.quote(symbol)}?{qs}"
    data = _get(url)
    if data is None:
        data = _get(f"{YAHOO_BASE2}/v8/finance/chart/{urllib.parse.quote(symbol)}?{qs}")
    result = (data or {}).get("chart", {}).get("result") or []
    if not result:
        raise RuntimeError(f"Yahoo returned no data for {symbol}")
    meta = result[0]
    ts = meta.get("timestamp") or []
    quotes = (meta.get("indicators", {}).get("quote") or [{}])[0]
    out = []
    for i, t in enumerate(ts):
        c = quotes.get("close")
        if not c or c[i] is None:
            continue
        out.append({
            "timestamp": int(t) * 1000,
            "open": quotes.get("open", [None] * len(ts))[i] or c[i],
            "high": quotes.get("high", [None] * len(ts))[i] or c[i],
            "low": quotes.get("low", [None] * len(ts))[i] or c[i],
            "close": float(c[i]),
            "volume": float(quotes.get("volume", [0] * len(ts))[i] or 0),
        })
    return out


def fetch_ohlcv(symbol: str, source: str, interval: str, start: Optional[str],
                end: Optional[str]) -> List[Dict[str, Any]]:
    start_ms = _parse_ts(start) if start else None
    end_ms = _parse_ts(end) if end else None
    if source == "binance":
        return fetch_binance(symbol, interval, start_ms, end_ms)
    return fetch_yahoo(symbol, interval, start_ms, end_ms)


def _parse_ts(text: str) -> int:
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except ValueError:
        return int(text)


# ---------------------------------------------------------------------------
# Indicators (kept testable - pure functions)
# ---------------------------------------------------------------------------

def sma(values: Sequence[float], period: int) -> List[Optional[float]]:
    out: List[Optional[float]] = [None] * len(values)
    acc = 0.0
    for i, v in enumerate(values):
        acc += v
        if i >= period:
            acc -= values[i - period]
        if i >= period - 1:
            out[i] = acc / period
    return out


def ema(values: Sequence[float], period: int) -> List[Optional[float]]:
    out: List[Optional[float]] = [None] * len(values)
    if not values:
        return out
    k = 2.0 / (period + 1)
    prev = values[0]
    out[0] = prev
    for i in range(1, len(values)):
        prev = values[i] * k + prev * (1 - k)
        out[i] = prev
    return out


def rsi(values: Sequence[float], period: int = 14) -> List[Optional[float]]:
    out: List[Optional[float]] = [None] * len(values)
    if len(values) <= period:
        return out
    gains = 0.0
    losses = 0.0
    for i in range(1, period + 1):
        chg = values[i] - values[i - 1]
        gains += max(chg, 0.0)
        losses += max(-chg, 0.0)
    avg_gain = gains / period
    avg_loss = losses / period
    out[period] = _rsi_from(avg_gain, avg_loss)
    for i in range(period + 1, len(values)):
        chg = values[i] - values[i - 1]
        gain = max(chg, 0.0)
        loss = max(-chg, 0.0)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        out[i] = _rsi_from(avg_gain, avg_loss)
    return out


def _rsi_from(avg_gain: float, avg_loss: float) -> float:
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def bollinger(values: Sequence[float], period: int = 20, mult: float = 2.0) -> Tuple[
        List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    mid = sma(values, period)
    upper: List[Optional[float]] = [None] * len(values)
    lower: List[Optional[float]] = [None] * len(values)
    for i in range(period - 1, len(values)):
        window = values[i - period + 1: i + 1]
        m = sum(window) / period
        var = sum((x - m) ** 2 for x in window) / period
        sd = math.sqrt(var)
        upper[i] = m + mult * sd
        lower[i] = m - mult * sd
    return upper, mid, lower


def atr(highs: Sequence[float], lows: Sequence[float], closes: Sequence[float],
        period: int = 14) -> List[Optional[float]]:
    out: List[Optional[float]] = [None] * len(closes)
    trs: List[float] = []
    for i in range(len(closes)):
        if i == 0:
            trs.append(highs[i] - lows[i])
        else:
            trs.append(max(highs[i] - lows[i],
                           abs(highs[i] - closes[i - 1]),
                           abs(lows[i] - closes[i - 1])))
    for i in range(period - 1, len(trs)):
        out[i] = sum(trs[i - period + 1: i + 1]) / period
    return out


def macd(values: Sequence[float], fast: int = 12, slow: int = 26,
         signal: int = 9) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    e_fast = ema(values, fast)
    e_slow = ema(values, slow)
    line: List[Optional[float]] = [None] * len(values)
    for i in range(len(values)):
        if e_fast[i] is not None and e_slow[i] is not None:
            line[i] = e_fast[i] - e_slow[i]
    sig_in = [v if v is not None else 0.0 for v in line]
    sig = ema(sig_in, signal)
    hist: List[Optional[float]] = [None] * len(values)
    for i in range(len(values)):
        if line[i] is not None and sig[i] is not None:
            hist[i] = line[i] - sig[i]
    return line, sig, hist


# ---------------------------------------------------------------------------
# Strategies: map series -> list of signals ("long"/"flat"/"short")
# ---------------------------------------------------------------------------

def _sma_cross(close: Sequence[float], fast: int = 20, slow: int = 50) -> List[str]:
    f = sma(close, fast)
    s = sma(close, slow)
    sigs: List[str] = ["flat"] * len(close)
    for i in range(slow, len(close)):
        if f[i] is None or s[i] is None or f[i - 1] is None or s[i - 1] is None:
            continue
        if f[i - 1] <= s[i - 1] and f[i] > s[i]:
            sigs[i] = "long"
        elif f[i - 1] >= s[i - 1] and f[i] < s[i]:
            sigs[i] = "short"
    return sigs


def _rsi_meanrev(close: Sequence[float], period: int = 14, oversold: float = 30,
                 overbought: float = 70) -> List[str]:
    r = rsi(close, period)
    sigs: List[str] = ["flat"] * len(close)
    for i in range(period, len(close)):
        rv = r[i]
        prev = r[i - 1] if i > 0 else None
        if rv is None:
            continue
        if prev is not None and prev <= oversold and rv > oversold:
            sigs[i] = "long"
        elif prev is not None and prev >= overbought and rv < overbought:
            sigs[i] = "short"
    return sigs


def _macd_strat(close: Sequence[float], fast: int = 12, slow: int = 26,
                signal: int = 9) -> List[str]:
    line, sig, _ = macd(close, fast, slow, signal)
    sigs: List[str] = ["flat"] * len(close)
    for i in range(slow + signal, len(close)):
        if line[i] is None or sig[i] is None or line[i - 1] is None or sig[i - 1] is None:
            continue
        if line[i - 1] <= sig[i - 1] and line[i] > sig[i]:
            sigs[i] = "long"
        elif line[i - 1] >= sig[i - 1] and line[i] < sig[i]:
            sigs[i] = "short"
    return sigs


def _bollinger_strat(close: Sequence[float], period: int = 20,
                     mult: float = 2.0) -> List[str]:
    upper, mid, lower = bollinger(close, period, mult)
    sigs: List[str] = ["flat"] * len(close)
    for i in range(period, len(close)):
        price = close[i]
        if upper[i] is None or lower[i] is None:
            continue
        if price <= lower[i]:
            sigs[i] = "long"
        elif price >= upper[i]:
            sigs[i] = "short"
    return sigs


STRATEGIES: Dict[str, Any] = {
    "sma_cross": {"fn": _sma_cross, "params": {"fast": 20, "slow": 50},
                  "desc": "SMA fast/slow crossover"},
    "rsi_meanrev": {"fn": _rsi_meanrev, "params": {"period": 14, "oversold": 30, "overbought": 70},
                    "desc": "RSI mean reversion"},
    "macd": {"fn": _macd_strat, "params": {"fast": 12, "slow": 26, "signal": 9},
             "desc": "MACD cross"},
    "bollinger": {"fn": _bollinger_strat, "params": {"period": 20, "mult": 2.0},
                  "desc": "Bollinger band bounce"},
}


def strategy_signals(name: str, close: Sequence[float], **kw) -> List[str]:
    if name not in STRATEGIES:
        raise ValueError(f"Unknown strategy '{name}'. Available: {sorted(STRATEGIES)}")
    meta = STRATEGIES[name]
    params = dict(meta["params"])
    params.update({k: v for k, v in kw.items() if v is not None})
    return meta["fn"](close, **params)


# ---------------------------------------------------------------------------
# Backtest engine
# ---------------------------------------------------------------------------

def run_backtest(rows: List[Dict[str, Any]], name: str, initial: float = 10_000.0,
                 fee: float = 0.1, **params) -> Dict[str, Any]:
    closes = [r["close"] for r in rows]
    signals = strategy_signals(name, closes, **params)
    cash = initial
    position = 0.0  # units held
    entry_px: Optional[float] = None
    trades: List[Dict[str, Any]] = []
    equity: List[float] = []
    fee_rate = fee / 100.0  # percent -> decimal, applied each side
    for i, sig in enumerate(signals):
        price = closes[i]
        if sig == "long" and position == 0:
            position = (cash * (1 - fee_rate)) / price
            cash = 0.0
            entry_px = price
            trades.append({"side": "long", "entry_idx": i, "entry_px": entry_px,
                           "qty": position, "ts": rows[i]["timestamp"]})
        elif sig == "flat" and position > 0:
            cash = position * price * (1 - fee_rate)
            _close_trade(trades[-1], i, price, fee_rate, rows[i]["timestamp"])
            position = 0.0
            entry_px = None
        elif sig == "short" and position > 0:
            cash = position * price * (1 - fee_rate)
            _close_trade(trades[-1], i, price, fee_rate, rows[i]["timestamp"])
            position = 0.0
            entry_px = None
        equity.append(cash + position * price)
    # Close open position at last price
    if position > 0 and trades:
        last_i = len(rows) - 1
        cash = position * closes[last_i] * (1 - fee_rate)
        _close_trade(trades[-1], last_i, closes[last_i], fee_rate,
                     rows[last_i]["timestamp"])
        equity[-1] = cash
    return _summarize(rows, name, initial, equity, trades)


def _close_trade(trade: Dict[str, Any], exit_i: int, exit_px: float,
                 fee: float, ts: int) -> None:
    trade["exit_idx"] = exit_i
    trade["exit_px"] = exit_px
    trade["exit_ts"] = ts
    trade["pnl_pct"] = round((exit_px / trade["entry_px"] - 1) * 100, 4)
    trade["net_pnl"] = round(
        (trade["qty"] * exit_px * (1 - fee)) - (trade["qty"] * trade["entry_px"]),
        4)


def _summarize(rows, name, initial, equity, trades) -> Dict[str, Any]:
    final = equity[-1] if equity else initial
    ret_pct = (final / initial - 1) * 100 if initial else 0.0
    max_dd = _max_drawdown(equity)
    win = [t for t in trades if t.get("net_pnl", 0) > 0]
    wins = len(win)
    total = len(trades)
    per = sum(t.get("net_pnl", 0) for t in trades)
    buy_hold = (rows[-1]["close"] / rows[0]["close"] - 1) * 100 if rows else 0.0
    avg_hold = 0
    if trades:
        hold_cells = [t.get("exit_idx", 0) - t.get("entry_idx", 0) for t in trades]
        avg_hold = round(sum(hold_cells) / len(hold_cells), 1)
    return {
        "strategy": name,
        "bars": len(rows),
        "initial_capital": round(initial, 2),
        "final_equity": round(final, 2),
        "total_return_pct": round(ret_pct, 2),
        "benchmark_buy_hold_pct": round(buy_hold, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "trades": total,
        "win_rate_pct": round((wins / total) * 100, 2) if total else 0.0,
        "total_fees_pnl": round(per, 2),
        "avg_hold_bars": avg_hold,
        "trade_log": trades,
        "start": rows[0]["timestamp"] if rows else None,
        "end": rows[-1]["timestamp"] if rows else None,
    }


def _max_drawdown(equity: Sequence[float]) -> float:
    peak = -math.inf
    dd = 0.0
    for v in equity:
        peak = max(peak, v)
        if peak > 0:
            dd = min(dd, (v - peak) / peak * 100)
    return dd


# ---------------------------------------------------------------------------
# CSV export + commands
# ---------------------------------------------------------------------------

def _write_csv(rows: List[Dict[str, Any]], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
        writer.writeheader()
        writer.writerows(rows)


def cmd_fetch(args: argparse.Namespace) -> None:
    rows = fetch_ohlcv(args.symbol, args.source, args.interval, args.start, args.end)
    if args.out:
        _write_csv(rows, args.out)
    if args.json:
        print(json.dumps({"count": len(rows), "rows": rows}, indent=2, default=str))
        return
    print(f"Fetched {len(rows)} bars for {args.symbol} ({args.source} {args.interval})")
    if rows:
        print(f"  first: {rows[0]['timestamp']} close={rows[0]['close']}")
        print(f"  last:  {rows[-1]['timestamp']} close={rows[-1]['close']}")


def cmd_backtest(args: argparse.Namespace) -> None:
    rows = fetch_ohlcv(args.symbol, args.source, args.interval, args.start, args.end)
    if len(rows) < 100:
        raise RuntimeError(f"Need >=100 bars for a meaningful backtest, got {len(rows)}")
    result = run_backtest(rows, args.strategy, args.initial, args.fee)
    if args.json:
        print(json.dumps(result, indent=2, default=str))
        return
    print(_format_result(result))


def cmd_compare(args: argparse.Namespace) -> None:
    rows = fetch_ohlcv(args.symbol, args.source, args.interval, args.start, args.end)
    if len(rows) < 100:
        raise RuntimeError(f"Need >=100 bars, got {len(rows)}")
    results = []
    for name in sorted(STRATEGIES):
        try:
            results.append(run_backtest(rows, name, args.initial, args.fee))
        except Exception as e:  # noqa: BLE001
            results.append({"strategy": name, "error": str(e)})
    results.sort(key=lambda r: r.get("total_return_pct", -math.inf), reverse=True)
    if args.json:
        print(json.dumps({"symbol": args.symbol, "results": results}, indent=2, default=str))
        return
    for r in results:
        line = (f"{r['strategy']:<14} ret={r['total_return_pct']:>8.2f}%  "
                f"dd={r['max_drawdown_pct']:>7.2f}%  win={r['win_rate_pct']:>6.2f}%  "
                f"trades={r['trades']}")
        if r.get("error"):
            line = f"{r['strategy']:<14} ERROR {r['error']}"
        print(line)


def cmd_optimize(args: argparse.Namespace) -> None:
    rows = fetch_ohlcv(args.symbol, args.source, args.interval, args.start, args.end)
    if len(rows) < 100:
        raise RuntimeError(f"Need >=100 bars, got {len(rows)}")
    grid: List[Dict[str, Any]] = []
    try:
        for part in (args.grid or "").split("|"):
            if not part:
                continue
            k, v = part.split("=", 1)
            grid.append((k.strip(), [float(x) for x in v.split(",")]))
    except ValueError:
        raise RuntimeError("--grid syntax: 'fast=10,20,30|slow=50,100'")
    if not grid:
        raise RuntimeError("--grid is required (e.g. 'fast=10,20,30|slow=40,50,60')")

    best = None
    combos = _product([vals for _, vals in grid])
    sweep = []
    for combo in combos:
        params = dict(zip([k for k, _ in grid], combo))
        res = run_backtest(rows, args.strategy, args.initial, args.fee, **params)
        sweep.append({"params": {k: _num(v) for k, v in params.items()},
                      "total_return_pct": res["total_return_pct"],
                      "max_drawdown_pct": res["max_drawdown_pct"],
                      "win_rate_pct": res["win_rate_pct"],
                      "trades": res["trades"]})
        if best is None or res["total_return_pct"] > best["total_return_pct"]:
            best = res
    sweep.sort(key=lambda s: s["total_return_pct"], reverse=True)
    if args.json:
        print(json.dumps({"strategy": args.strategy, "best": sweep[0] if sweep else None,
                          "sweep": sweep}, indent=2, default=str))
        return
    print(f"Optimizing {args.strategy} over {len(sweep)} combos")
    if sweep:
        b = sweep[0]
        print(f"  best: {b['params']} ret={b['total_return_pct']:.2f}% dd={b['max_drawdown_pct']:.2f}%")
    for s in sweep[:10]:
        print(f"    {s['params']} -> ret={s['total_return_pct']:.2f}% win={s['win_rate_pct']:.2f}% trades={s['trades']}")


def cmd_download(args: argparse.Namespace) -> None:
    rows = fetch_ohlcv(args.symbol, args.source, args.interval, args.start, args.end)
    _write_csv(rows, args.out)
    print(f"Wrote {len(rows)} bars to {args.out}")


def _num(v: float) -> Any:
    return int(v) if float(v).is_integer() else v


def _product(groups: Sequence[Sequence[float]]) -> List[Tuple[float, ...]]:
    result: List[Tuple[float, ...]] = [()]
    for group in groups:
        result = [prev + (v,) for prev in result for v in group]
    return result


def _format_result(r: Dict[str, Any]) -> str:
    return (
        f"Strategy      : {r['strategy']}\n"
        f"Bars          : {r['bars']} ({r['start']} -> {r['end']})\n"
        f"Initial       : ${r['initial_capital']:,.2f}\n"
        f"Final equity  : ${r['final_equity']:,.2f}\n"
        f"Total return  : {r['total_return_pct']:+.2f}%\n"
        f"Buy & hold    : {r['benchmark_buy_hold_pct']:+.2f}%\n"
        f"Max drawdown  : {r['max_drawdown_pct']:.2f}%\n"
        f"Trades        : {r['trades']} (win rate {r['win_rate_pct']}%)\n"
        f"Avg hold      : {r['avg_hold_bars']} bars\n"
        f"Gross PnL     : ${r['total_fees_pnl']:,.2f}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="backtester",
        description="Multi-market algorithmic trading backtester (crypto, stocks, forex).",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    for name in ("fetch", "backtest", "compare", "optimize", "download"):
        p = sub.add_parser(name, help=f"{name} a symbol")
        p.add_argument("symbol")
        p.add_argument("--source", default="binance", choices=["binance", "yahoo"])
        p.add_argument("--interval", default="1d", choices=sorted(INTERVALS))
        p.add_argument("--start", default=None, help="ISO date or epoch ms")
        p.add_argument("--end", default=None, help="ISO date or epoch ms")
        p.add_argument("--json", action="store_true")
        p.add_argument("--out", default=None)
        p.add_argument("--initial", type=float, default=10_000.0)
        p.add_argument("--fee", type=float, default=0.1, help="per-trade fee percent")
        if name == "backtest":
            p.add_argument("--strategy", default="sma_cross", choices=sorted(STRATEGIES))
        if name == "optimize":
            p.add_argument("--strategy", default="sma_cross", choices=sorted(STRATEGIES))
            p.add_argument("--grid", required=True,
                           help="pairs, e.g. 'fast=10,20,30|slow=50,60,70'")
        p.set_defaults(extra=name)
    return parser


DISPATCH = {
    "fetch": cmd_fetch,
    "download": cmd_download,
    "backtest": cmd_backtest,
    "compare": cmd_compare,
    "optimize": cmd_optimize,
}


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    fn = DISPATCH.get(args.command)
    if fn is None:
        print(json.dumps({"error": f"Unknown command '{args.command}'"}))
        return 1
    try:
        fn(args)
    except KeyboardInterrupt:
        print(json.dumps({"error": "Interrupted by user"}))
        return 130
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())