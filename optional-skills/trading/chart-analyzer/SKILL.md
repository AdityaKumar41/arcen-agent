---
name: chart-analyzer
description: "Automated chart & market context analyzer for any symbol."
version: 1.0.0
author: Arcen Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  arcen:
    tags: [trading, charts, analysis, technical-indicators, btc, markets, support-resistance]
    category: trading
    related_skills: [backtester, stocks, hyperliquid]
    requires_toolsets: [terminal]
---

# Chart & Market Context Analyzer Skill

Automatically pulls recent OHLCV for any symbol (crypto via Binance, stocks
and forex via Yahoo), computes technical indicators (RSI, MACD, EMA/SMA,
Bollinger, ATR), support/resistance, volume ratio, and emits a structured
"market context" JSON. The agent then turns that context into a plain-language
brief on current market behavior.

It analyzes charts only — it does **not** place trades or give financial advice.

---

## When to Use

- User asks "what is the market doing right now" for BTC, ETH, a stock, or EUR/USD
- User wants a technical read: trend direction, overbought/oversold, key levels
- User wants recent support/resistance to frame an entry/exit
- User wants a reproducible snapshot of indicators for a symbol to discuss

---

## Prerequisites

Python 3.8+ standard library only — no pip installs.

Data sources (free, no key): Binance public REST (crypto), Yahoo chart API
(stocks/forex).

Optional overrides:
```bash
export BINANCE_API_URL=https://api.binance.com/api/v3
```

Helper script path: `~/.arcen/skills/trading/chart-analyzer/scripts/chart_analyzer.py`

---

## How to Run

```bash
python3 ~/.arcen/skills/trading/chart-analyzer/scripts/chart_analyzer.py <symbol> [options]
```

Pass `--json` for machine-readable context.

---

## Quick Reference

```
SCRIPT=~/.arcen/skills/trading/chart-analyzer/scripts/chart_analyzer.py

python3 $SCRIPT BTCUSDT                          # crypto (Binance), 200 daily bars
python3 $SCRIPT BTCUSDT --interval 4h --limit 300
python3 $SCRIPT EURUSD=X --source yahoo          # forex
python3 $SCRIPT AAPL --source yahoo --interval 1d
python3 $SCRIPT BTCUSDT --json                   # structured context for scripting
```

---

## Procedure

### 1. Get Market Context

```bash
python3 $SCRIPT BTCUSDT --json
```

The command prints (human or JSON):
- **Trend** — bullish / bearish based on SMA50/SMA200 vs EMA20 vs price
- **RSI14** — value + zone (overbought / oversold / strong / weak / neutral)
- **MACD** — line vs signal, cross type (bullish/bearish/none)
- **SMA50 / SMA200 / EMA20** values
- **Bollinger** — upper/mid/lower + band position (0-100%)
- **ATR14** — volatility as % of price
- **Support / resistance** — from recent swing highs/lows
- **Volume ratio** — current vs 20-bar average
- **24h change** and a one-line summary

### 2. Turn Context Into a Brief

Read the JSON/human output and write a concise narrative: trend, momentum
(RSI/MACD), key levels to watch, and volatility. State uncertainty explicitly
(e.g., "RSI neutral, MACD just crossed bullish, watching resistance at X").

---

## Pitfalls

- **Public RPC/API limits** — Binance throttles unauthed klines; Yahoo may
  return empty for obscure tickers. Retries handle 429s; keep `--limit`
  moderate.
- **Support/resistance are heuristics** — swing-based levels over the trailing
  window; they are zones, not guarantees. Combine with macro context.
- **Live data** — indicators are computed from the snapshot; they move. Cite
  the `timestamp` in any summary.
- **Not advice** — this is a technical snapshot. Do not present it as a
  recommendation or guarantee of price direction.

---

## Verification

```bash
# Should print trend, RSI zone, support/resistance
python3 ~/.arcen/skills/trading/chart-analyzer/scripts/chart_analyzer.py BTCUSDT

# Structured JSON path
python3 ~/.arcen/skills/trading/chart-analyzer/scripts/chart_analyzer.py BTCUSDT --json
```