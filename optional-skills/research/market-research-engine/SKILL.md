---
name: market-research-engine
description: "Automated market research, RSS, and sentiment engine."
version: 1.0.0
author: Arcen Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  arcen:
    tags: [research, market-analysis, sentiment, rss, competitors, insights]
    category: research
    related_skills: [agent-reach, coin-deep-dive]
    requires_toolsets: [terminal, web]
---

# Research & Market Analytics Engine Skill

Intelligence system that aggregates real-time data (RSS), tracks competitors,
and runs lexicon sentiment over recent coverage to automate deep-dive market
research and actionable insights. Outputs a structured "research pack" the
agent turns into a brief.

Stdlib only — no external NLP libraries, no API keys.

---

## When to Use

- User wants a deep-dive market brief on a company/product/sector
- User wants to monitor live RSS/headlines on a topic with sentiment
- User wants a competitor matrix and positioning notes
- User wants one combined "research pack" to write up

---

## Prerequisites

Python 3.8+ standard library only — no pip installs.

Helper script path: `~/.arcen/skills/research/market-research-engine/scripts/market_research.py`

---

## How to Run

```bash
SCRIPT=~/.arcen/skills/research/market-research-engine/scripts/market_research.py

python3 $SCRIPT brief "solana etf" --context "launch week"
python3 $SCRIPT rss --feeds "https://feeds.feedburner.com/coindesk" --limit 20
python3 $SCRIPT sentiment --file headlines.txt
python3 $SCRIPT competitors comps.json
python3 $SCRIPT pack "solana etf" --feeds "https://..." --competitors comps.json --out pack.json
```

---

## Procedure

1. **Brief** — `brief <topic>` prints the research brief template (objective,
   questions, sources, deliverables). Fill it as you go.
2. **Aggregate** — `rss --feeds url1,url2` pulls live items with per-item
   sentiment labels.
3. **Sentiment** — `sentiment --file text` scores overall + per-sentence
   polarity over a built-in lexicon and lists top terms.
4. **Competitors** — `competitors comps.json` builds a matrix and positioning
   suggestions.
5. **Pack** — `pack <topic> --feeds ... --competitors ... --out pack.json`
   assembles everything (brief + headlines + sentiment + competitors + top
   terms) into one research pack for the write-up.

---

## Quick Reference

```
SCRIPT=~/.arcen/skills/research/market-research-engine/scripts/market_research.py
python3 $SCRIPT brief "ai chips"
python3 $SCRIPT rss --feeds "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml" --limit 10
python3 $SCRIPT sentiment "Beats estimates. Strong growth. Shares surge."
python3 $SCRIPT pack "ai chips" --competitors comps.json --feeds "https://..." --out pack.json
```

`comps.json` input rows: `{"name":"Nvidia","category":"AI","rating":4.8,"mentions":120,"notes":"..."}`

---

## Pitfalls

- **Lexicon sentiment is a proxy** — it scores word polarity, not nuance
  (sarcasm, "not bad", compare-vs-absolute). Treat labels as directional.
- **RSS feed reliability** — feeds rotate; wrap `rss` per-feed and tolerate
  one bad feed (it reports per-item errors in JSON mode).
- **Competitor ratings/mentions are input facts** — validate them with web
  research before quoting in a brief.
- **Coverage ≠ truth** — high mention share means loud, not right. Cross-check
  insights before recommending.

---

## Verification

```bash
# Should label this positive
python3 ~/.arcen/skills/research/market-research-engine/scripts/market_research.py \
  sentiment "Strong growth beats expectations, record profits"
```