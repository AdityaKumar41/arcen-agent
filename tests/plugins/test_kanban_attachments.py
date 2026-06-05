"""Tests for Kanban task file attachments (#35338).

Covers three layers:
  * ``arcen_cli.kanban_db`` accessors (add/list/get/delete + path helpers)
  * worker-context surfacing so a kanban worker sees the absolute paths
"""

from __future__ import annotations

from pathlib import Path

import pytest

from arcen_cli import kanban_db as kb


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def kanban_home(tmp_path, monkeypatch):
    home = tmp_path / ".arcen"
    home.mkdir()
    monkeypatch.setenv("ARCEN_HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    kb.init_db()
    return home


def _make_task(conn, title="t") -> str:
    return kb.create_task(conn, title=title)


# ---------------------------------------------------------------------------
# DB-layer accessors
# ---------------------------------------------------------------------------


def test_add_list_get_delete_attachment(kanban_home, tmp_path):
    conn = kb.connect()
    try:
        task_id = _make_task(conn)
        # Write a real blob under the per-task dir so delete can unlink it.
        dest_dir = kb.task_attachments_dir(task_id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        blob = dest_dir / "source.pdf"
        blob.write_bytes(b"%PDF-1.4 fake")

        att_id = kb.add_attachment(
            conn,
            task_id,
            filename="source.pdf",
            stored_path=str(blob),
            content_type="application/pdf",
            size=blob.stat().st_size,
            uploaded_by="tester",
        )
        assert att_id > 0

        atts = kb.list_attachments(conn, task_id)
        assert len(atts) == 1
        a = atts[0]
        assert a.filename == "source.pdf"
        assert a.content_type == "application/pdf"
        assert a.size == len(b"%PDF-1.4 fake")
        assert a.uploaded_by == "tester"
        assert a.stored_path == str(blob)

        got = kb.get_attachment(conn, att_id)
        assert got is not None and got.id == att_id

        removed = kb.delete_attachment(conn, att_id)
        assert removed is not None and removed.id == att_id
        assert kb.list_attachments(conn, task_id) == []
        assert not blob.exists(), "delete should unlink the on-disk blob"
        assert kb.get_attachment(conn, att_id) is None
    finally:
        conn.close()


def test_add_attachment_rejects_unknown_task(kanban_home):
    conn = kb.connect()
    try:
        with pytest.raises(ValueError):
            kb.add_attachment(
                conn, "t_doesnotexist", filename="x.txt", stored_path="/tmp/x.txt"
            )
    finally:
        conn.close()


def test_add_attachment_appends_event(kanban_home):
    conn = kb.connect()
    try:
        task_id = _make_task(conn)
        kb.add_attachment(
            conn, task_id, filename="a.txt", stored_path="/tmp/a.txt", size=3
        )
        kinds = [e.kind for e in kb.list_events(conn, task_id)]
        assert "attached" in kinds
    finally:
        conn.close()


def test_delete_attachment_missing_returns_none(kanban_home):
    conn = kb.connect()
    try:
        assert kb.delete_attachment(conn, 999999) is None
    finally:
        conn.close()


def test_attachments_root_is_per_board(kanban_home, monkeypatch):
    # default board uses <root>/kanban/attachments
    default_root = kb.attachments_root(board="default")
    assert default_root.name == "attachments"
    # a named board nests under its board dir
    monkeypatch.delenv("ARCEN_KANBAN_ATTACHMENTS_ROOT", raising=False)
    named = kb.attachments_root(board="default")
    assert named == default_root


def test_attachments_root_env_override(kanban_home, monkeypatch, tmp_path):
    override = tmp_path / "custom-attach"
    monkeypatch.setenv("ARCEN_KANBAN_ATTACHMENTS_ROOT", str(override))
    assert kb.attachments_root() == override
    assert kb.task_attachments_dir("t_abc") == override / "t_abc"


# ---------------------------------------------------------------------------
# Worker context surfacing
# ---------------------------------------------------------------------------


def test_worker_context_lists_attachments_with_absolute_path(kanban_home):
    conn = kb.connect()
    try:
        task_id = _make_task(conn, title="translate PDF")
        dest_dir = kb.task_attachments_dir(task_id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        blob = dest_dir / "manual.pdf"
        blob.write_bytes(b"data")
        kb.add_attachment(
            conn,
            task_id,
            filename="manual.pdf",
            stored_path=str(blob.resolve()),
            content_type="application/pdf",
            size=4,
        )
        ctx = kb.build_worker_context(conn, task_id)
        assert "## Attachments" in ctx
        assert "manual.pdf" in ctx
        # The absolute path must appear so the worker can read_file it.
        assert str(blob.resolve()) in ctx
    finally:
        conn.close()


def test_worker_context_no_attachments_section_when_empty(kanban_home):
    conn = kb.connect()
    try:
        task_id = _make_task(conn)
        ctx = kb.build_worker_context(conn, task_id)
        assert "## Attachments" not in ctx
    finally:
        conn.close()
