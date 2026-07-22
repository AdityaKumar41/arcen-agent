"""Unit tests for self-evolution (agent/evolution.py).

Run with:
    bash scripts/run_tests.sh tests/agent/test_evolution.py
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from agent.evolution import analyze_and_evolve_skill


class TestEvolution:
    def test_evolve_nonexistent_skill_returns_error(self, tmp_path):
        with patch("agent.evolution.extract_skills_dir", return_value=tmp_path):
            ok, report, content = analyze_and_evolve_skill("nonexistent-skill")
            assert ok is False
            assert "not found" in report
            assert content is None

    def test_evolve_skill_applies_optimizations(self, tmp_path):
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: "Test skill"
---
# Test Skill
Do test things.
""", encoding="utf-8")

        with patch("agent.evolution.extract_skills_dir", return_value=tmp_path):
            ok, report, updated = analyze_and_evolve_skill("test-skill")
            assert ok is True
            assert "Successfully evolved" in report
            assert updated is not None
            assert "GEPA/DSPy Refinements" in updated
            assert "Error Handling" in updated
