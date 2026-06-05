"""Regression tests for _apply_profile_override ARCEN_HOME guard (issue #22502).

When ARCEN_HOME is set to the arcen root (e.g. systemd hardcodes
ARCEN_HOME=/root/.arcen), _apply_profile_override must still read
active_profile and update ARCEN_HOME to the profile directory.

When ARCEN_HOME is already a profile directory (.../profiles/<name>),
_apply_profile_override must trust it and return without re-reading
active_profile (child-process inheritance contract).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path



def _run_apply_profile_override(
    tmp_path, monkeypatch, *, arcen_home: str | None, active_profile: str | None,
    argv: list[str] | None = None,
):
    """Run _apply_profile_override in isolation.

    Returns the value of os.environ["ARCEN_HOME"] after the call,
    or None if unset.
    """
    arcen_root = tmp_path / ".arcen"
    arcen_root.mkdir(parents=True, exist_ok=True)

    if active_profile is not None:
        (arcen_root / "active_profile").write_text(active_profile)

    if active_profile and active_profile != "default":
        (arcen_root / "profiles" / active_profile).mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    if arcen_home is not None:
        monkeypatch.setenv("ARCEN_HOME", arcen_home)
    else:
        monkeypatch.delenv("ARCEN_HOME", raising=False)

    monkeypatch.setattr(sys, "argv", argv or ["arcen", "gateway", "start"])

    from arcen_cli.main import _apply_profile_override
    _apply_profile_override()

    return os.environ.get("ARCEN_HOME")


class TestApplyProfileOverrideArcenHomeGuard:
    """Regression guard for issue #22502.

    Verifies that ARCEN_HOME pointing to the arcen root does NOT suppress
    the active_profile check, while ARCEN_HOME already pointing to a
    profile directory IS trusted as-is.
    """

    def test_arcen_home_at_root_with_active_profile_is_redirected(
        self, tmp_path, monkeypatch
    ):
        """ARCEN_HOME=/root/.arcen + active_profile=coder must redirect
        ARCEN_HOME to .../profiles/coder.

        Bug scenario from #22502: systemd sets ARCEN_HOME to the arcen root
        and the user switches to a profile via `arcen profile use`.
        Before the fix, the guard returned early and active_profile was ignored.
        """
        arcen_root = tmp_path / ".arcen"
        arcen_root.mkdir(parents=True, exist_ok=True)

        result = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            arcen_home=str(arcen_root),
            active_profile="coder",
        )

        assert result is not None, "ARCEN_HOME must be set after profile redirect"
        assert "profiles" in result, (
            f"Expected ARCEN_HOME to point into profiles/ dir, got: {result!r}"
        )
        assert result.endswith("coder"), (
            f"Expected ARCEN_HOME to end with 'coder', got: {result!r}"
        )

    def test_arcen_home_already_profile_dir_is_trusted(self, tmp_path, monkeypatch):
        """ARCEN_HOME=.../profiles/coder must not be overridden even when
        active_profile says something different.

        Preserves the child-process inheritance contract: a subprocess spawned
        with ARCEN_HOME already set to a specific profile must stay in that
        profile.
        """
        arcen_root = tmp_path / ".arcen"
        profile_dir = arcen_root / "profiles" / "coder"
        profile_dir.mkdir(parents=True, exist_ok=True)

        (arcen_root / "active_profile").write_text("other")

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("ARCEN_HOME", str(profile_dir))
        monkeypatch.setattr(sys, "argv", ["arcen", "gateway", "start"])

        from arcen_cli.main import _apply_profile_override
        _apply_profile_override()

        assert os.environ.get("ARCEN_HOME") == str(profile_dir), (
            "ARCEN_HOME must remain unchanged when already pointing to a profile dir"
        )

    def test_arcen_home_unset_reads_active_profile(self, tmp_path, monkeypatch):
        """Classic case: ARCEN_HOME unset + active_profile=coder must set
        ARCEN_HOME to the profile directory (existing behaviour must not regress).
        """
        result = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            arcen_home=None,
            active_profile="coder",
        )

        assert result is not None
        assert "coder" in result

    def test_arcen_home_unset_default_profile_no_redirect(self, tmp_path, monkeypatch):
        """active_profile=default must not redirect ARCEN_HOME."""
        arcen_root = tmp_path / ".arcen"
        arcen_root.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("ARCEN_HOME", raising=False)
        monkeypatch.setattr(sys, "argv", ["arcen", "gateway", "start"])
        (arcen_root / "active_profile").write_text("default")

        from arcen_cli.main import _apply_profile_override
        _apply_profile_override()

        assert os.environ.get("ARCEN_HOME") is None
