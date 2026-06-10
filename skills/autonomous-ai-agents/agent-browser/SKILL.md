---
name: agent-browser
description: Use Agent Browser skills for browser work.
version: 1.0.0
author: Arcen Agent
license: MIT
platforms: [linux, macos]
metadata:
  arcen:
    tags: [agent-browser, browser, automation, web, skills]
    category: autonomous-ai-agents
    related_skills: [dogfood, find-skills]
---

# Agent Browser Skill

Use this skill when a task should lean on Agent Browser's browser automation workflows or its own skill library. Agent Browser ships runtime skill instructions, so fetch the current instructions from the installed CLI instead of copying stale guidance into the conversation.

This skill complements Arcen's native browser tools. Use the native browser toolset for direct page interaction, and use Agent Browser when the user asks for Agent Browser specifically or when its workflow skills are a better fit.

## When to Use

- The user mentions Agent Browser, `agent-browser`, or agent-browser.dev.
- The user wants browser automation skills from the Agent Browser project.
- The task involves Electron, Slack, Vercel Sandbox, AgentCore, or browser-agent dogfooding workflows covered by Agent Browser skills.
- You need current Agent Browser instructions rather than a fixed local summary.

## Prerequisites

- Use the `terminal` tool when command execution is needed.
- The `agent-browser` CLI should be available in the active environment.
- Network access may be needed for initial package resolution or updates.
- For direct page interaction inside Arcen, the native browser toolset can still be used.

## How to Run

Ask the installed CLI for its current skill catalog:

```bash
agent-browser skills list --json
```

Load the current instructions for a specific Agent Browser skill:

```bash
agent-browser skills get core --full
agent-browser skills get dogfood --full
agent-browser skills get electron --full
agent-browser skills get slack --full
agent-browser skills get vercel-sandbox --full
agent-browser skills get agentcore --full
```

Find the local skill file path when you need to inspect linked files:

```bash
agent-browser skills path core
```

## Quick Reference

| Goal | Command |
|---|---|
| Show active runtime instructions | `agent-browser skills` |
| List available skills | `agent-browser skills list --json` |
| Read a short skill summary | `agent-browser skills get <name>` |
| Read full instructions | `agent-browser skills get <name> --full` |
| Read every bundled instruction | `agent-browser skills get --all` |
| Locate skill files | `agent-browser skills path [name]` |

Known Agent Browser skill names include `core`, `dogfood`, `electron`, `slack`, `vercel-sandbox`, and `agentcore`. Verify with `agent-browser skills list --json` before relying on the list.

## Procedure

1. Confirm the task is an Agent Browser task or would benefit from its runtime skills.
2. List available Agent Browser skills:
   ```bash
   agent-browser skills list --json
   ```
3. Pick the closest skill. Use `core` for general browser work when there is no narrower match.
4. Load full current instructions:
   ```bash
   agent-browser skills get <name> --full
   ```
5. Follow those instructions for the task, using Arcen tools where they match the workflow.
6. If the user wants the Agent Browser skill installed into their broader agent ecosystem, use the find-skills workflow and the skills.sh-compatible command:
   ```bash
   npx skills add vercel-labs/agent-browser
   ```
7. Report which Agent Browser skill was used and any setup gaps found.

## Pitfalls

- Do not rely on this file as the full Agent Browser manual. Pull current instructions from `agent-browser skills get <name> --full`.
- Do not install `vercel-labs/agent-browser` without the user's intent; loading local runtime instructions is usually enough.
- If `agent-browser` is unavailable, say so and continue with Arcen's native browser tools when the task can still be completed.
- If the Agent Browser skill output conflicts with user instructions, follow the user's task boundaries.

## Verification

- `agent-browser skills list --json` returns the expected skill names.
- `agent-browser skills get core --full` returns current runtime guidance.
- The selected Agent Browser skill matches the task domain.
- Any optional install with `npx skills add vercel-labs/agent-browser` completes only after user approval.
