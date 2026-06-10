---
name: find-skills
description: Find and install agent skills.
version: 1.0.0
author: Arcen Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  arcen:
    tags: [skills, discovery, install, skills-sh]
    category: productivity
    related_skills: [arcen-agent-skill-authoring]
---

# Find Skills Skill

Use this skill when a user wants to discover, compare, preview, install, audit, or update agent skills. Prefer Arcen's built-in skills hub first, because it scans installs and already knows about skills.sh, well-known agent skill endpoints, GitHub, ClawHub, browse.sh, and official optional skills.

This skill does not replace manual review. Third-party skills can change agent behavior, so preview and audit before trusting them.

## When to Use

- The user asks if a skill exists for a task.
- The user wants to install a skill from skills.sh, GitHub, a direct URL, or another registry.
- The user mentions `skills.sh`, `find-skills`, `npx skills`, agent skills, or skill discovery.
- The user wants to list, update, audit, uninstall, or snapshot installed skills.
- The current task would benefit from a specialized workflow that might already exist.

## Prerequisites

- Use the `terminal` tool when command execution is needed.
- Prefer the local Arcen CLI from the active environment, such as `arcen` or `.venv/bin/arcen`.
- Network access may be required for remote registries.
- A `GITHUB_TOKEN` in the Arcen env can improve GitHub registry rate limits, but it is optional.

## How to Run

Use Arcen's skills hub as the default path:

```bash
arcen skills search "<query>" --source all
arcen skills browse --source skills-sh
arcen skills inspect <identifier>
arcen skills install <identifier>
arcen skills list
arcen skills audit <name>
```

If the user specifically asks for the open skills CLI ecosystem, use the `terminal` tool to run the `npx skills` command they requested, for example:

```bash
npx skills add vercel-labs/skills
```

Do this only when it fits the user's request or when Arcen's hub cannot resolve the skill.

## Quick Reference

| Goal | Preferred command |
|---|---|
| Search every registry | `arcen skills search "<query>" --source all` |
| Search skills.sh only | `arcen skills search "<query>" --source skills-sh` |
| Browse skills.sh | `arcen skills browse --source skills-sh` |
| Preview before install | `arcen skills inspect <identifier>` |
| Install a skill | `arcen skills install <identifier>` |
| Re-scan installed skills | `arcen skills audit [name]` |
| Check updates | `arcen skills check` |
| Update skills | `arcen skills update [name]` |
| Snapshot installs | `arcen skills snapshot export` |

## Procedure

1. Clarify the task in one sentence if the user only gives a broad domain.
2. Search skills.sh first for public discovery:
   ```bash
   arcen skills search "<task or domain>" --source skills-sh
   ```
3. If results are thin, search all registries:
   ```bash
   arcen skills search "<task or domain>" --source all
   ```
4. Preview the best candidate before installing:
   ```bash
   arcen skills inspect <identifier>
   ```
5. Summarize the skill's purpose, source, trust signals, and any setup requirements.
6. Install only after the user clearly wants it installed:
   ```bash
   arcen skills install <identifier>
   ```
7. Audit installed third-party skills when risk matters:
   ```bash
   arcen skills audit <name>
   ```
8. After installation, tell the user the skill name and how to invoke it naturally.

## Pitfalls

- Do not install a third-party skill silently. Preview first unless the user explicitly requested a direct install.
- Do not assume a skills.sh leaderboard entry is safe enough by itself.
- Do not confuse bundled Arcen skills with hub-installed skills. `arcen skills list` shows both.
- Use full identifiers when search returns multiple skills with the same name.
- If `npx skills` and `arcen skills` disagree, trust the command that matches the user's requested ecosystem and report the difference.

## Verification

- `arcen skills search find-skills --source skills-sh` returns a relevant skills.sh result.
- `arcen skills inspect <identifier>` shows a readable `SKILL.md`.
- `arcen skills install <identifier>` completes and records the install in the hub lockfile.
- `arcen skills list` shows the installed skill.
- `arcen skills audit <name>` reports no unexpected high-risk findings before production use.
