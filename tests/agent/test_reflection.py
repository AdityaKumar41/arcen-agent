"""Unit tests for reflective trajectory learning (agent/reflection.py).

Run with:
    bash scripts/run_tests.sh tests/agent/test_reflection.py
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from agent.reflection import reflect_and_distill_skill, extract_skills_dir


class TestReflection:
    def test_extract_skills_dir_creates_path(self, tmp_path):
        with patch("agent.reflection.get_arcen_home", return_value=str(tmp_path)):
            skills_dir = extract_skills_dir()
            assert skills_dir.exists()
            assert skills_dir.name == "skills"

    def test_reflect_with_empty_messages_returns_error(self):
        ok, msg, path = reflect_and_distill_skill([])
        assert ok is False
        assert "No conversation history" in msg
        assert path is None

    def test_reflect_generates_skill_file(self, tmp_path):
        messages = [
            {"role": "user", "content": "How to deploy FastAPI on Docker?"},
            {"role": "assistant", "content": "Here is the Dockerfile and command steps for FastAPI deployment."},
        ]

        with patch("agent.reflection.get_arcen_home", return_value=str(tmp_path)):
            ok, msg, path = reflect_and_distill_skill(messages, skill_name="fastapi-docker")
            assert ok is True
            assert path is not None
            assert path.exists()
            assert "fastapi-docker" in str(path)
            content = path.read_text(encoding="utf-8")
            assert "name: fastapi-docker" in content
            assert "FastAPI" in content
