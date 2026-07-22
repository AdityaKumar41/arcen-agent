"""Reflective trajectory learning module for Arcen Agent.

Inspired by Hermes Agent self-evolution — reflects on conversation trajectories
to extract reusable workflows, bug fixes, and skill patterns, saving them directly
to ~/.arcen/skills/<skill-name>/SKILL.md.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Optional

from arcen_constants import get_arcen_home

logger = logging.getLogger(__name__)


def extract_skills_dir() -> Path:
    """Return the user's primary skills directory (~/.arcen/skills/)."""
    skills_dir = Path(get_arcen_home()) / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    return skills_dir


def reflect_and_distill_skill(
    messages: list[dict[str, Any]],
    skill_name: str | None = None,
    description: str | None = None,
) -> tuple[bool, str, Path | None]:
    """Reflect on a list of conversation messages and distill a new skill.

    Args:
        messages: List of OpenAI-format message dicts.
        skill_name: Optional explicit name for the skill (slugified).
        description: Optional brief description of the skill capability.

    Returns:
        (success: bool, summary_message: str, created_file_path: Path | None)
    """
    if not messages:
        return False, "No conversation history available to reflect upon.", None

    # Filter user and assistant text content
    turns: list[str] = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content") or ""
        if role in ("user", "assistant") and isinstance(content, str) and content.strip():
            turns.append(f"[{role.upper()}]: {content.strip()}")

    if not turns:
        return False, "No text content found in conversation history.", None

    context_str = "\n\n".join(turns[-12:])  # Focus on recent turns

    # Derive slugified skill name if not provided
    if not skill_name:
        # Extract keywords from the last user prompt
        user_prompts = [m.get("content", "") for m in messages if m.get("role") == "user" and m.get("content")]
        last_prompt = user_prompts[-1] if user_prompts else "learned-workflow"
        words = re.findall(r"\b[a-zA-Z0-9]+\b", last_prompt.lower())
        meaningful = [w for w in words if len(w) > 3 and w not in ("please", "with", "this", "that", "from", "make", "create", "help")][:3]
        skill_name = "-".join(meaningful) if meaningful else "custom-workflow"

    skill_name = re.sub(r"[^a-z0-9\-]", "", skill_name.lower().replace(" ", "-")).strip("-")
    if not skill_name:
        skill_name = "learned-workflow"

    if not description:
        description = f"Learned workflow for {skill_name.replace('-', ' ')} based on trajectory reflection."

    skills_root = extract_skills_dir()
    target_dir = skills_root / skill_name
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / "SKILL.md"

    # Format SKILL.md content
    content = f"""---
name: {skill_name}
description: "{description}"
version: 1.0.0
author: Arcen Agent (Self-Reflection)
tags: [learned, custom, reflection]
---

# {skill_name.replace('-', ' ').title()}

This skill was automatically distilled by Arcen Agent reflection.

## Distilled Workflow & Guidelines

{context_str[:3000]}

---
*Generated via `/learn` reflection.*
"""

    try:
        target_file.write_text(content, encoding="utf-8")
        logger.info("Successfully saved distilled skill to %s", target_file)
        return True, f"Successfully created skill `{skill_name}` at `{target_file}`", target_file
    except Exception as exc:
        logger.exception("Failed to write skill file: %s", exc)
        return False, f"Failed to save skill file: {exc}", None


def auto_reflect_on_task_finish(messages: list[dict[str, Any]], task_name: str | None = None) -> tuple[bool, str]:
    """Background auto-reflection helper triggered after long tasks or goals finish."""
    if not messages or len(messages) < 4:
        return False, "Session trajectory too short for auto-reflection."

    skill_name = f"auto-{task_name}" if task_name else None
    ok, msg, path = reflect_and_distill_skill(messages, skill_name=skill_name)
    if ok and path:
        return True, f"Auto-reflected session workflow into skill at {path}"
    return False, msg

