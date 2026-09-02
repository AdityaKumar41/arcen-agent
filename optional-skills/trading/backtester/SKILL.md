---
name: backtester
description: "Multi-market strategy backtester (crypto, stocks, forex)."
version: 1.0.0
author: Arcen Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  arcen:
    tags: [trading, backtest, crypto, stocks, forex, algorithmic, indicators, quantitative]
    category: trading
    related_skills: [chart-analyzer, hyperliquid]
    requires_toolsets: [terminal]
---

# Trading Backtester Skill

Backtest algorithmic trading strategies across crypto (Binance), stocks, and
forex (Yahoo Finance) using free public OHLCV data. Four indicator strategies
(SMA crossover, RSI mean-reversion, MACD cross, Bollinger bounce), a
strategy-vs-strategy comparator, parameter grid optimization, and CSV export.
Python standard library only — no external dependencies, no API keys.

It tests and compares strategies historically; it does **not** place trades or
fetch live quotes.

---

## When to Use

- User wants to backtest "buy when SMA 20 crosses above SMA 50" on BTC, AAPL, or EUR/USD
- User wants to compare multiple strategies on the same symbol and pick a winner
- User wants to sweep strategy parameters (e.g., find the best SMA periods)
- User wants historical OHLCV data exported to CSV for their own analysis
- User wants an idea of max drawdown, win rate, and trade count for a strategy

---

## Prerequisites

Python 3.8+ standard library only — no pip installs.

Data sources (free, no key):
- Crypto: Binance public REST (`https://api.binance.com/api/v3/klines`)
- Stocks/forex: Yahoo Finance chart API (interval `1d`/`1h` etc.)

Optional overrides:
```bash
export BINANCE_API_URL=https://api.binance.com/api/v3   # proxied endpoint
```

Helper script path: `~/.arcen/skills/trading/backtester/scripts/backtester.py`

---

## How to Run

```bash
python3 ~/.arcen/skills/trading/backtester/scripts/backtester.py <command> [options]
```

Every command accepts `--json` for machine-readable output.

---

## Quick Reference

```
SCRIPT=~/.arcen/skills/trading/backtester/scripts/backtester.py

# Backtest a single strategy
python3 $SCRIPT backtest BTCUSDT --source binance --interval 1d --strategy sma_cross
python3 $SCRIPT backtest AAPL   --source yahoo    --interval 1d --strategy rsi_meanrev
python3 $SCRIPT backtest EURUSD=X --source yahoo  --strategy macd --start 2023-01-01

# Compare all strategies on one symbol
python3 $SCRIPT compare BTCUSDT --interval 1d

# Parameter optimization (pipe-separated param=value-list)
python3 $SCRIPT optimize BTCUSDT --strategy sma_cross \
  --grid "fast=10,20,30|slow=50,60,70"

# Raw OHLCV export
python3 $SCRIPT download BTCUSDT --out hourly.csv --interval 1h --start 2024-01-01
python3 $SCRIPT fetch BTCUSDT --interval 1h --out check.csv

# JSON for scripting / further analysis
python3 $SCRIPT backtest BNBBTC --json
```

---

## Procedure

### 1. Backtest a Single Strategy
```bash
python3 $SCRIPT backtest BTCUSDT --strategy sma_cross --interval 1d --fee 0.1
```
- `--initial` sets starting capital (default 10,000).
- `--fee` is the per-side fee percent (default 0.1; add taker fees, slippage).
- `--start`/`--end` accept ISO dates (`2024-01-01`) or epoch milliseconds.
- Requires ≥100 bars; prints return %, buy-and-hold benchmark, max drawdown,
  win rate, trade count, average holding bars, and the full trade log.

### 2. Strategies
| Name | Logic | Default params |
|---|---|---|
| `sma_cross` | Long on fast/below→above, flat on reverse | fast 20, slow 50 |
| `rsi_meanrev` | Long when RSI recovers from <30, flat on >70 rollover | period 14, 30/70 |
| `macd` | Long/short on MACD line/signal cross | 12/26/9 |
| `bollinger` | Long at lower band, flat at upper band | 20, 2.0 |

### 3. Compare Strategies
```bash
python3 $SCRIPT compare BTCUSDT
```
Runs all four strategies on the same data and ranks by total return, with
drawdown/win-rate next to each.

### 4. Optimize Parameters
```bash
python3 $SCRIPT optimize BTCUSDT --strategy sma_cross \
  --grid "fast=5,10,15|slow=30,50,70"
```
Sweeps the full cross-product of the grid, reports the best combo and a top-10
table. Always validate an optimized strategy on out-of-sample data.

### 5. Export Data
```bash
python3 $SCRIPT download BTCUSDT --out btc_daily.csv --interval 1d
```
Exports raw OHLCV (`timestamp,open,high,low,close,volume`) for pandas/Excel/other tools.

---

## Pitfalls

- **Overfitting** — optimizing the grid until it prints a high return usually
  means curve-fitting noise. Split into train/test (optimize on one window,
  verify on another) before trusting it.
- **Buy-and-hold bias** — a strategy that rarely trades can beat a winning
  strategy on return alone while underperforming on volatility-adjusted terms.
  Use drawdown and win rate, not just return.
- **Data gaps** — Yahoo symbols for forex use `EURUSD=X`; delisted/obscure
  tickers return no data. Binance requires base-quote symbol format (`BTCUSDT`,
  `BTCBUSD` not supported after delisting).
- **Feed realism** — backtests assume fills at bar close. Real slippage adds up
  on meme/liquid-void pairs. Include a higher `--fee` for realistic results.
- **Interval support** — Binance supports minute/hour intervals; Yahoo chart
  approximates long ranges. For `4h` Yahoo data, use `--interval 4h`
  (mapped to daily).
- **Rate limits** — Binance throttles unauthed klines; retries handle 429s but
  very long ranges may need batching.

---

## Verification

```bash
# Should print strategy stats (trades, return, drawdown)
python3 ~/.arcen/skills/trading/backtester/scripts/backtester.py \
  backtest BTCUSDT --strategy sma_cross

# Should output a ranked strategy table
python3 ~/.arcen/skills/trading/backtester/scripts/backtester.py compare BTCUSDT
```