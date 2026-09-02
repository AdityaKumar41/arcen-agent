---
name: coin-deep-dive
description: "Score any coin on tokenomics, utility, on-chain, team."
version: 1.0.0
author: Arcen Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  arcen:
    tags: [crypto, tokenomics, audit, coin, scorecard, on-chain, utility]
    category: blockchain
    related_skills: [funding-dive, evm, coingecko]
    requires_toolsets: [terminal, web]
---

# Coin Deep-Analysis Engine Skill

Granular audit of a cryptocurrency across five weighted dimensions: tokenomics,
utility, on-chain metrics, team, and technical architecture. Pulls live
supply/market/funding facts from CoinGecko, combines them with a 0-10 rubric
the agent scores via web research, and produces a graded deep-dive report with
red flags.

Stdlib only. Read-only.

---

## When to Use

- User wants a scored deep-dive on a coin before deciding anything
- User wants tokenomics red flags (unreleased supply, no max supply, low float)
- User wants a reproducible scorecard across coins to compare candidates
- User wants the exact research question set a rubric should answer

---

## Prerequisites

Python 3.8+ standard library only — no pip installs. CoinGecko free API (no key).

Helper script path: `~/.arcen/skills/blockchain/coin-deep-dive/scripts/coin_deep_dive.py`

Optional overrides:
```bash
export COINGECKO_API_URL=https://api.coingecko.com/api/v3
```

---

## How to Run

```bash
SCRIPT=~/.arcen/skills/blockchain/coin-deep-dive/scripts/coin_deep_dive.py

python3 $SCRIPT template --out research.json        # scoring rubric template
# fill research.json with 0-10 scores from web research, then:
python3 $SCRIPT analyze bitcoin --research-file research.json
python3 $SCRIPT analyze pepe --categories meme --json          # offline mode
python3 $SCRIPT analyze solana --fail-fast                     # online only
```

---

## Scoring Rubric (weights)

| Dimension | Weight | Sample 0-10 cues |
|---|---|---|
| tokenomics | 25% | supply cap, emission, allocations, staking |
| utility | 25% | real use cases, revenue flywheel, demand |
| on-chain | 20% | active users, fees, TVL, holders |
| team | 15% | founders, track record, transparency, known identity |
| architecture | 15% | consensus, decentralization, throughput, upgrades |

Grade bands: A≥8, B≥6.5, C≥5, D≥3.5, F<3.5. Category adjustment: meme/fan-token
penalty (-1.0), product-category bonus (+0.5).

---

## Analyze Output

- CoinGecko facts: price, supply, mcap/fdv, ATH, github stats, categories
- **Flags**: low float vs max supply, no max supply, no public github,
  missing rubric dimensions
- Weighted dimension scores, category adjustment, final score, grade

---

## Pitfalls

- **CoinGecko query can fail offline** — without `--fail-fast`, analysis falls
  back to the research file (or `--categories`); the report then flags missing
  on-chain facts. Supply flags are only available when online.
- **Robustness of self-scores** — the rubric is scored by the researcher
  (agent). Cite evidence per dimension in the research file so scores are
  reviewable, not vibes.
- **Category penalty is a heuristic** — a serious meme project can still be a
  real business; treat the score as one input, not a verdict.
- **Descriptions/supply change** — the report is a snapshot; note the timestamp
  when quoting it.

---

## Verification

```bash
python3 ~/.arcen/skills/blockchain/coin-deep-dive/scripts/coin_deep_dive.py \
  analyze bitcoin --json   # should print market facts + a score
```