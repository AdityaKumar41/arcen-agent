---
name: coingecko
description: "Global crypto market data, top coins, movers, prices."
version: 1.0.0
author: Arcen Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  arcen:
    tags: [Crypto, Market, Prices, CoinGecko, Blockchain, Defi, Trending, Gainers, Losers]
    category: blockchain
    related_skills: [evm, solana, hyperliquid]
    requires_toolsets: [terminal]
---

# CoinGecko Crypto Market Skill

Read-only crypto market data via the free CoinGecko API. Seven commands:
global market overview, top coins by market cap, trending searches, 24h
gainers/losers, category rankings, and multi-coin price lookups. No API key
and no external dependencies (Python standard library only).

It reports market-wide and per-coin data; it does **not** read wallets, place
trades, or query on-chain balances. Use `evm`, `solana`, or `hyperliquid` for
wallet/chain-level queries.

---

## When to Use

- User asks how the whole crypto market is doing (total cap, 24h volume, BTC dominance)
- User wants the current top 10/100 coins by market cap
- User wants today's biggest gainers or losers
- User asks what's trending on CoinGecko right now
- User wants a price check for one or several coins (e.g. "price of BTC and ETH")
- User wants crypto sector/category rankings (DeFi, Layer 2, Meme, etc.)
- User wants market data in another currency (EUR, JPY, BTC-denominated prices)

---

## Prerequisites

Python 3.8+ standard library only — no pip installs.

The helper uses CoinGecko's **free public API** (no key). Free-tier limits are
roughly 5–30 requests/minute; occasional `429 Too Many Requests` responses are
retried internally with backoff.

Helper script path: `~/.arcen/skills/blockchain/coingecko/scripts/coingecko_client.py`

Optional overrides:

```bash
export COINGECKO_API_URL=https://api.coingecko.com/api/v3   # proxied/self-hosted endpoint
```

---

## How to Run

```bash
python3 ~/.arcen/skills/blockchain/coingecko/scripts/coingecko_client.py <command> [options]
```

Everything prints human-readable tables by default; pass `--json` for
machine-readable output (normalized keys, suitable for piping into other work).

---

## Quick Reference

```
SCRIPT=~/.arcen/skills/blockchain/coingecko/scripts/coingecko_client.py

# Global market
python3 $SCRIPT market                          # total cap, 24h vol, BTC/ETH dominance
python3 $SCRIPT market --convert eur            # same, in EUR

# Top coins
python3 $SCRIPT top                             # top 10 by market cap (USD)
python3 $SCRIPT top --limit 25 --vs usd
python3 $SCRIPT top --order volume_desc         # top by 24h volume instead

# Movers
python3 $SCRIPT gainers                         # today's biggest 24h gainers
python3 $SCRIPT losers --limit 20

# Trending
python3 $SCRIPT trending

# Categories
python3 $SCRIPT categories --limit 15

# Prices
python3 $SCRIPT price BTC,ETH
python3 $SCRIPT price doge,sol,ada --vs eur
python3 $SCRIPT price "Bitcoin"                 # unknown name -> /search fallback

# JSON for scripting
python3 $SCRIPT top --limit 5 --json
python3 $SCRIPT price BTC,ETH --json
```

---

## Procedure

### 1. Global Market Overview
```bash
python3 $SCRIPT market
```
Prints active coin count, total market cap, 24h volume, 24h market-cap change,
and BTC/ETH dominance percentages. `--convert` switches the reporting currency.

### 2. Top Coins by Market Cap
```bash
python3 $SCRIPT top --limit 25
```
Ranks coins by market cap (default USD). Includes price, 24h change, and market
cap. `--order` accepts `market_cap_asc`, `volume_desc`, `gecko_desc`,
`gecko_asc`, `id_asc`, `id_desc`. Max 250 per call.

### 3. 24h Gainers / Losers
```bash
python3 $SCRIPT gainers
python3 $SCRIPT losers --limit 20
```
Fetches the top 100 coins by market cap and sorts them locally by 24h percent
change (this avoids relying on CoinGecko's per-plan `percent_change` ordering).

### 4. Trending Searches
```bash
python3 $SCRIPT trending
```
The coins most-searched on CoinGecko right now, with their search scores.

### 5. Category Rankings
```bash
python3 $SCRIPT categories --limit 20
```
Sector-level view (DeFi, Layer 1, Meme tokens, etc.) sorted by market cap, with
24h change. Helpful for narrative/momentum scanning.

### 6. Multi-Coin Prices
```bash
python3 $SCRIPT price BTC,ETH,SOL
python3 $SCRIPT price bitcoin,ethereum   # explicit CoinGecko ids also work
```
Accepts comma-separated symbols or CoinGecko ids. Known tickers resolve
offline; anything else falls back to the `/search` endpoint so names like
"solana" or obscure coins still resolve. Output includes 24h change.

---

## Pitfalls

- **Free-tier rate limits** — CoinGecko throttles unauthed requests (~5–30/min).
  The script retries `429` responses with exponential backoff, but heavy
  terminal loops can still hit the ceiling. Space out calls or use a
  proxied/pro key via `COINGECKO_API_URL`.
- **Symbols are not unique** — CoinGecko allows multiple coins to share a
  ticker. Only a curated list of well-known symbols (`BTC`, `ETH`, `USDC`,
  `SOL`, ...) is resolved directly; any other input goes through `/search`,
  which may return a different project you intended.
- **Day-over-day changes can be missing** — `gainers`/`losers` filter out coins
  with no 24h change data, so counts may under-report on thin pairs.
- **Live data** — market cap, volume, and changes are snapshots; they move
  constantly. Never treat reported values as settled facts for legal/financial
  decisions.
- **Endpoint shape** — the `/global` and `/coins/categories` endpoints return
  currency-keyed maps; `--convert btc`/`eth` renders BTC/ETH-denominated
  figures with higher precision.

---

## Verification

```bash
# Should print total market cap and BTC dominance
python3 ~/.arcen/skills/blockchain/coingecko/scripts/coingecko_client.py market

# Should print BTC's current price and 24h change
python3 ~/.arcen/skills/blockchain/coingecko/scripts/coingecko_client.py price BTC
```