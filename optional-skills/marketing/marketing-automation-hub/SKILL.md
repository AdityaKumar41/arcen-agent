---
name: marketing-automation-hub
description: "Plan, track, and report multi-channel campaigns."
version: 1.0.0
author: Arcen Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  arcen:
    tags: [marketing, automation, content-calendar, campaigns, dashboards, crm, scheduling]
    category: marketing
    related_skills: [influencer-analyzer, b2b-lead-generation]
    requires_toolsets: [terminal, cronjob]
---

# Marketing Automation Hub Skill

End-to-end marketing orchestrator: define campaigns across channels, generate
a content calendar, track publish status, record per-channel performance, and
produce a dashboard with insights — all from a workspace-backed JSON store.

This hub manages the **plan and the metrics**. Executing content (posting to
platforms) happens via the relevant platform tools or integrations; the agent
uses this hub to stay coherent and measure results.

---

## When to Use

- User wants a multi-channel content calendar for a campaign
- User wants to track what was published vs scheduled
- User wants to log channel performance and see which channel converts best
- User wants an automated marketing dashboard + recommendations

---

## Prerequisites

Python 3.8+ standard library only — no pip installs.

Helper script path: `~/.arcen/skills/marketing/marketing-automation-hub/scripts/marketing_hub.py`

Data persists to a JSON workspace (default: `~/.arcen/skills/marketing/marketing-automation-hub/workspace/`); override with `--workdir`.

---

## How to Run

```bash
SCRIPT=~/.arcen/skills/marketing/marketing-automation-hub/scripts/marketing_hub.py

python3 $SCRIPT init
python3 $SCRIPT add-campaign --name "Q3 Launch" --goal awareness \
  --channels social,newsletter --cadence weekdays --start 2026-01-05
python3 $SCRIPT plan --name "Q3 Launch" --days 60
python3 $SCRIPT metric --channel social --period 2026-01 \
  --impressions 500000 --clicks 12000 --conversions 300 --spend 2000 --revenue 9000
python3 $SCRIPT report
```

---

## Procedure

1. **Init** — `init` creates the workspace.
2. **Campaign** — `add-campaign` (channels, cadence, goal, audience).
3. **Plan** — `plan` generates a calendar item per channel per day honoring the
   cadence (`daily` / `weekdays` / `weekly` / `biweekly`).
4. **Execute** — post content via platform tools (xurl, slack, etc.); mark
   each item `scheduled`/`published` with `mark`.
5. **Measure** — log per-channel performance per period with `metric`.
6. **Report** — `report` aggregates CTR, conversion rate, ROAS, CPA, ranks
   channels, flags best/worst, and prints actionable insights.

---

## Quick Reference

```
python3 $SCRIPT init
python3 $SCRIPT add-campaign --name Q3 --channels social,newsletter --cadence weekdays
python3 $SCRIPT plan --name Q3 --days 30 --json
python3 $SCRIPT status
python3 $SCRIPT mark --name Q3 --date 2026-01-06 --channel social --status published
python3 $SCRIPT metric --channel newsletter --impressions 80000 --clicks 4000 --conversions 120
python3 $SCRIPT report --json
```

---

## Pitfalls

- **Metrics are self-reported** — record what your platform analytics give you.
  Inconsistent `period` values fragment the report; use ISO week/month keys.
- **Calendar is a plan, not a promise** — update `mark`/`status` as things
  actually happen, or `report` will overstate intent.
- **Multi-user edits** — the store is a single JSON file; serialize writes
  (one agent/human at a time) to avoid lost updates.
- **Not a scheduler daemon** — for true scheduled posting, pair this plan with
  `arcen cron` / the `cronjob` tool to emit reminders or run post steps.

---

## Verification

```bash
# Should print a channel ranking + insights after logging some metrics
python3 ~/.arcen/skills/marketing/marketing-automation-hub/scripts/marketing_hub.py report
```