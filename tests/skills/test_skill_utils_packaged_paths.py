from pathlib import Path

from agent.skill_utils import is_excluded_skill_path


def test_packaged_skills_under_venv_are_not_excluded() -> None:
    path = (
        Path("/tmp/app/venv")
        / "skills"
        / "productivity"
        / "find-skills"
        / "SKILL.md"
    )
    assert not is_excluded_skill_path(path)


def test_cache_dirs_inside_skills_root_are_excluded() -> None:
    path = Path("/tmp/app/venv") / "skills" / ".hub" / "index-cache" / "SKILL.md"
    assert is_excluded_skill_path(path)


def test_external_virtualenv_paths_are_still_excluded() -> None:
    path = Path("/tmp/project/.venv/lib/python/site-packages/demo/SKILL.md")
    assert is_excluded_skill_path(path)
