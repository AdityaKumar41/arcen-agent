---
name: b2b-lead-generation
description: "Prospect, verify, score, and sequence B2B leads."
version: 1.0.0
author: Arcen Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  arcen:
    tags: [b2b, leads, prospecting, outreach, crm, sales, enrichment]
    category: marketing
    related_skills: [marketing-automation-hub]
    requires_toolsets: [terminal]
---

# Automated B2B Lead Generation Pipeline Skill

Multi-channel prospecting and enrichment engine: build lead records from seed
companies, verify contacts (syntax, disposable, role accounts), score by
firmographic + intent fit, build a personalized multi-touch outreach cadence,
and export to CSV or HubSpot-style JSON for sync.

**Discovery/enrichment of exact contacts is upstream** (web/search tools). This
pipeline runs the dedup / verify / score / sequence / export stages.

---

## When to Use

- User wants to turn a target-company list into a prioritized lead pipeline
- User wants email quality checks before sending
- User wants a repeatable outreach cadence per lead
- User wants a CRM-ready export

---

## Prerequisites

Python 3.8+ standard library only — no pip installs.

Helper script path: `~/.arcen/skills/marketing/b2b-lead-generation/scripts/b2b_lead_gen.py`

Store: JSON at `~/.arcen/skills/marketing/b2b-lead-generation/leads.json` (override `--store`).

---

## How to Run

```bash
SCRIPT=~/.arcen/skills/marketing/b2b-lead-generation/scripts/b2b_lead_gen.py

python3 $SCRIPT prospect "Acme,FabCorp,Initech" --source linkedin --industry fintech
python3 $SCRIPT prospect companies.txt
python3 $SCRIPT verify --json
python3 $SCRIPT score
python3 $SCRIPT sequence --company Acme --touches 5
python3 $SCRIPT export --out leads.csv --format csv
python3 $SCRIPT export --out leads.json --format hubspot
```

---

## Procedure

1. **Prospect** — seed companies from a comma list or file. Add per-lead
   fields later (name, email, role, employees, funding_usd, intent, tech_stack).
2. **Verify** — checks email syntax, disposable domains, and role-account
   prefixes; flags `invalid`, `flag_role`, `block_disposable`, or `ok`.
3. **Score** — firmographic (size, funding) + intent keywords + verification
   status into a `score` (0-100) and bucket (`hot`/`warm`/`cold`).
4. **Sequence** — build a multi-touch cadence (email/linkedin mix) with
   personalization hooks per lead.
5. **Export** — CSV or HubSpot-style JSON for CRM sync.

---

## Output

- `verify` → counts + flagged rows.
- `score` → ranked table with `bucket` and `score_reasons`.
- `sequence` → per-lead cadence with day offsets and subject templates.
- `export` → CRM-ready file.

---

## Pitfalls

- **Verification is local heuristics** — syntax/disposable/role checks catch
  obvious cases, not deliverability. Use an MX/engagement check service for a
  hard verdict on important lists.
- **Email ≠ consent** — outreach still needs sending consent and list hygiene;
  don't blast a scraped list.
- **Self-supplied data** — `employees`, `funding_usd`, `intent` drive the
  score; verify firmographic claims with web research before heavy spend.
- **Store is append + enrich** — run `verify`/`score` after `prospect` and
  after any enrichment so rankings reflect the latest data.

---

## Verification

```bash
SCRIPT=~/.arcen/skills/marketing/b2b-lead-generation/scripts/b2b_lead_gen.py
python3 $SCRIPT prospect "Acme" --source test
# then edit leads.json to add a contact email, then:
python3 $SCRIPT verify && python3 $SCRIPT score --json
```