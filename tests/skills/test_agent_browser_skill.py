import re
from pathlib import Path


SKILL_MD = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "autonomous-ai-agents"
    / "agent-browser"
    / "SKILL.md"
)


def _read() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def test_agent_browser_frontmatter_description_is_short() -> None:
    text = _read()
    match = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
    assert match is not None
    description = match.group(1).strip().strip('"')
    assert len(description) <= 60
    assert description.endswith(".")


def test_agent_browser_references_runtime_skill_commands() -> None:
    text = _read()
    assert "agent-browser skills list --json" in text
    assert "agent-browser skills get core --full" in text
    assert "agent-browser skills path core" in text
    assert "npx skills add vercel-labs/agent-browser" in text


def test_agent_browser_names_documented_bundled_skills() -> None:
    text = _read()
    for name in [
        "core",
        "dogfood",
        "electron",
        "slack",
        "vercel-sandbox",
        "agentcore",
    ]:
        assert name in text


def test_agent_browser_has_modern_sections() -> None:
    text = _read()
    sections = [
        "## When to Use",
        "## Prerequisites",
        "## How to Run",
        "## Quick Reference",
        "## Procedure",
        "## Pitfalls",
        "## Verification",
    ]
    positions = [text.index(section) for section in sections]
    assert positions == sorted(positions)
