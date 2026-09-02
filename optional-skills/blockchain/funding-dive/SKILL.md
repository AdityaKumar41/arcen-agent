---
name: funding-dive
description: "Funding rounds, investors, and vesting deep-dive."
version: 1.0.0
author: Arcen Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  arcen:
    tags: [crypto, funding, venture-capital, vesting, tokenomics, investor, deep-dive]
    category: blockchain
    related_skills: [coin-deep-dive, evm]
    requires_toolsets: [terminal]
---

# Crypto Investment & Funding Rounds Deep-Dive Skill

Track and analyze VC funding rounds for crypto projects: record rounds
(amount, valuation, investors, sector, token allocation), compute token
vesting schedules from standard models, measure investor concentration, and
aggregate early-stage capital inflows by sector.

Stdlib only. Local JSON tracker + optional CoinGecko enrichment.

---

## When to Use

- User wants a funding deep-dive on a project (timeline, raise sizes, investors)
- User wants to estimate a token's vesting/unlock schedule from a round's
  allocation and standard model
- User wants to know which investors lead a deal (concentration)
- User wants a sector-level view of where early-stage capital is flowing

---

## Prerequisites

Python 3.8+ standard library only — no pip installs.

Helper script path: `~/.arcen/skills/blockchain/funding-dive/scripts/funding_dive.py`

Store: JSON at `~/.arcen/skills/blockchain/funding-dive/funding.json` (override `--store`).

Optional enrichment (no key): `gecko <coin>` pulls project facts from
CoinGecko to seed a new project record.

---

## How to Run

```bash
SCRIPT=~/.arcen/skills/blockchain/funding-dive/scripts/funding_dive.py

python3 $SCRIPT add Acme --date 2024-01-10 --round seed --amount 5000000 \
  --investors "a16z,Pantera" --sector defi --token-alloc 8
python3 $SCRIPT add Acme --date 2024-09-01 --round private --amount 20000000 \
  --investors "a16z,Polychain" --sector defi --valuation 250000000
python3 $SCRIPT analyze Acme
python3 $SCRIPT analyze Acme --vesting seed        # full unlock table
python3 $SCRIPT sectors --json
python3 $SCRIPT list
python3 $SCRIPT gecko ethereum
```

---

## Standard Vesting Models

| Round | TGE % | Cliff | Duration |
|---|---|---|---|
| seed | 10% | 6mo | 24mo |
| private | 15% | 6mo | 24mo |
| strategic | 10% | 12mo | 36mo |
| public | 30% | 1mo | 12mo |

`token-allocation` (% of supply sold in that round) drives the token-denominated
schedule; `analyze --vesting <round>` prints the per-month unlock table.

---

## Analyzer Output

- total raised, round count, latest round + valuation
- top investor and share (concentration: diversified / moderate / high)
- per-round recap with model release @ 12 months
- vesting table on request

---

## Pitfalls

- **Vesting is a model, not fact** — actual schedules live in the tokenomics
  docs/token contract. Confirm TGE/cliff/duration before quoting unlocks.
- **Big raises ≠ good** — analyze investor quality and valuation together (a
  huge raise at a huge valuation is dilution-heavy).
- **Equity vs token** — `--round equity` means no token allocation; don't mix
  token-denominated and equity ideas in the same analysis.
- **Investor data is self-entered** — validate names and amounts against
  primary sources (round announcements) before relying on them.

---

## Verification

```bash
SCRIPT=~/.arcen/skills/blockchain/funding-dive/scripts/funding_dive.py
python3 $SCRIPT add Demo --date 2025-01-01 --round seed --amount 3000000 \
  --investors "Galaxy" --sector infra --token-alloc 10
python3 $SCRIPT analyze Demo --vesting seed   # should show TGE on day 1, cliff 6mo
```