---
name: influencer-analyzer
description: "Rank creators and plan campaigns for any product."
version: 1.0.0
author: Arcen Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  arcen:
    tags: [marketing, influencers, creators, campaigns, engagement, ctr, hooks]
    category: marketing
    related_skills: [agent-reach, marketing-automation-hub]
    requires_toolsets: [terminal]
---

# Influencer & Campaign Marketing Analyzer Skill

Ingests a discovery file (creators + engagement + sample content), scores each
creator against a product brief, extracts their top marketing hooks, and
produces a ranked shortlist plus a concrete campaign plan.

**Discovery is upstream:** gather the creator data with web/search tooling
(agent-reach is ideal for X/TikTok/YouTube/etc.). This skill turns that raw
data into rankings and a plan.

---

## When to Use

- User wants to find which creators to work with for a product launch
- User wants creators ranked by engagement, reach, CTR, and niche fit
- User wants the 2-3 best hooks to reuse in a campaign
- User wants a tiered campaign plan (anchor / co-signal / amplifier)

---

## Prerequisites

Python 3.8+ standard library only — no pip installs. Fully offline once the
creators file exists.

Helper script path: `~/.arcen/skills/marketing/influencer-analyzer/scripts/influencer_analyzer.py`

---

## How to Run

```bash
python3 ~/.arcen/skills/marketing/influencer-analyzer/scripts/influencer_analyzer.py \
  template --out creators.json                      # get the shape
python3 ~/.arcen/skills/marketing/influencer-analyzer/scripts/influencer_analyzer.py \
  analyze creators.json --product "Hydra Face Serum" --niche skincare --budget 5000
```

Add `--json` for machine-readable output.

---

## Quick Reference

```
SCRIPT=~/.arcen/skills/marketing/influencer-analyzer/scripts/influencer_analyzer.py

python3 $SCRIPT template --out creators.json
python3 $SCRIPT analyze creators.json --product "3D printer for kids" --niche education
python3 $SCRIPT analyze creators.csv --product "SaaS note app" --budget 20000 --json
```

Input shape (`creators.json`):

```json
{
  "product": "Hydra Face Serum",
  "niche": "skincare",
  "budget": 5000,
  "creators": [
    {
      "name": "Jane Creator", "platform": "tiktok", "handle": "@jane",
      "followers": 250000, "avg_engagement": 17500, "ctr": 3.2,
      "topics": "skincare, beauty", "est_cost": 900,
      "sample_posts": ["3 skincare mistakes that age you faster", "Why I stopped using chemical sunscreen"]
    }
  ]
}
```

---

## Procedure

1. **Discover** — gather 8-15 creators in the niche via web/agent-reach:
   platform, handle, follower count, avg engagement, CTR (if available),
   estimated cost, and 3-5 sample post begins/hooks.
2. **Template** — `template --out creators.json` to get the exact JSON shape,
   then fill it with collected data.
3. **Analyze** — `analyze creators.json --product "..." --niche ... --budget ...`
4. **Use the output** — the ranked shortlist (with `weighed_score`), each
   creator's top hooks, the tiered campaign plan, and a recommendation. Draft
   outreach from the hooks column.

---

## Output & Scoring

`weighed_score` = `engagement_rate% * 60 + ctr * 8 + hook_score * 3 + niche_fit * 10`.
Ranked descending. The campaign plan assigns the top 3 as anchor / co-signal /
amplifier with roles, deliverables, and measurement KPIs per tier.

---

## Pitfalls

- **Self-reported CTR** — only trust CTR you measured or took from a real
  media kit; otherwise treat it as 0 and let engagement + reach drive score.
- **Follower count is vanity** — engagement rate and niche fit matter more;
  the scoring weights them accordingly.
- **Sample posts matter** — the hook scorer reads the first-line framing of
  `sample_posts`. Include real openings, not titles.
- **Not a talent agency** — the output is analytics; negotiation, contracts,
  and legal review are still human steps.

---

## Verification

```bash
# Should print a ranked table + campaign plan
python3 ~/.arcen/skills/marketing/influencer-analyzer/scripts/influencer_analyzer.py \
  analyze creators.json --product "Sample product" --niche tech
```