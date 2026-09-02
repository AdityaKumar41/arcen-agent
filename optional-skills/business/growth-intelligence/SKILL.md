---
name: growth-intelligence
description: "Unit economics scoring and growth recommendations."
version: 1.0.0
author: Arcen Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  arcen:
    tags: [business, growth, saas, cac, ltv, churn, unit-economics, metrics]
    category: business
    related_skills: [ecommerce-optimizer]
    requires_toolsets: [terminal]
---

# Business Growth Intelligence Engine Skill

Holistic analytics over a metrics JSON: computes unit economics (CAC, LTV,
LTV:CAC, churn, payback, NRR, growth), scores business health across domains
with a flag system, generates prioritized growth recommendations, and drafts a
90-day plan.

Stdlib only. Fully offline once the metrics file exists.

---

## When to Use

- User wants to understand their unit economics / SaaS health from raw numbers
- User wants a health check across acquisition, retention, expansion
- User wants prioritized, actionable growth recommendations
- User wants a 90-day growth plan

---

## Prerequisites

Python 3.8+ standard library only — no pip installs.

Helper script path: `~/.arcen/skills/business/growth-intelligence/scripts/growth_intelligence.py`

---

## How to Run

```bash
SCRIPT=~/.arcen/skills/business/growth-intelligence/scripts/growth_intelligence.py

python3 $SCRIPT template --out metrics.json
python3 $SCRIPT report metrics.json
python3 $SCRIPT report metrics.json --json
```

---

## Procedure

1. **Template** — `template --out metrics.json` writes the input shape.
2. **Fill** — put in your real numbers (customers, new/churned monthly,
   revenue, ARR, gross margin, marketing/sales spend, NRR).
3. **Report** — computes unit economics, health flags per domain, and
   recommendations tied to the flags:
   - LTV:CAC vs the 3:1 target
   - payback months
   - monthly churn vs 2%/5% bands
   - NRR vs 100/110 bands
   - customer growth rate
4. **Plan** — the 90-day roadmap (stabilize → optimize → scale) is driven by
   the critical areas.

---

## Metrics Input (all optional except revenue-ish numbers)

```json
{
  "customers": 1200,
  "new_customers_monthly": 60,
  "churned_customers_monthly": 18,
  "monthly_revenue": 96000,
  "arr": 1152000,
  "gross_margin": 0.8,
  "monthly_marketing_spend": 15000,
  "monthly_sales_spend": 5000,
  "nrr": 108
}
```

Defaults applied when missing: gross margin 80%, and ARR derived from revenue.
If a metric is missing, the related health check is skipped (not guessed).

---

## Pitfalls

- **Garbage in, garbage out** — churn/acqui numbers must be real; the engine
  will confidently present conclusions from the inputs you give.
- **One model, one context** — SaaS unit-economics framing; adapt numbers for
  other business models (cash-based, marketplace, hardware) manually.
- **Recommended, not required** — the recommendations are rule-driven; weigh
  them against your strategic priorities and capital.
- **Lag vs lead** — NRR forward-looking, churn lagging. Trust expansion flags
  for growth trajectory.

---

## Verification

```bash
# Should print unit economics + health + recommendations
python3 ~/.arcen/skills/business/growth-intelligence/scripts/growth_intelligence.py \
  template --out metrics.json
python3 ~/.arcen/skills/business/growth-intelligence/scripts/growth_intelligence.py \
  report metrics.json
```