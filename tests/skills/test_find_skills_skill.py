import re
from pathlib import Path


SKILL_MD = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "productivity"
    / "find-skills"
    / "SKILL.md"
)


def _read() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def test_find_skills_frontmatter_description_is_short() -> None:
    text = _read()
    match = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
    assert match is not None
    description = match.group(1).strip().strip('"')
    assert len(description) <= 60
    assert description.endswith(".")


def test_find_skills_defaults_to_arcen_and_skills_sh() -> None:
    text = _read()
    assert "arcen skills search" in text
    assert "arcen skills inspect" in text
    assert "arcen skills install" in text
    assert "--source skills-sh" in text
    assert "skills.sh" in text
    assert "npx skills add vercel-labs/skills" in text


def test_find_skills_has_modern_sections() -> None:
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
