"""Tests for built-in memory history and restore commands."""

import json
from types import SimpleNamespace

from tools.memory_tool import MemoryStore, get_memory_history_path


def _events():
    path = get_memory_history_path()
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_memory_store_records_history_for_mutations(monkeypatch, tmp_path):
    monkeypatch.setenv("ARCEN_HOME", str(tmp_path))

    store = MemoryStore(memory_char_limit=500, user_char_limit=500)
    store.load_from_disk()

    assert store.add("memory", "Project uses pytest.")["success"]
    assert store.replace("memory", "pytest", "Project uses pytest via scripts/run_tests.sh.")["success"]
    assert store.remove("memory", "scripts/run_tests")["success"]

    events = _events()
    assert [event["action"] for event in events] == ["add", "replace", "remove"]
    assert events[0]["actor"] == "agent"
    assert events[0]["target"] == "memory"
    assert events[0]["old"] is None
    assert events[0]["new"] == "Project uses pytest."
    assert events[1]["old"] == "Project uses pytest."
    assert events[1]["new"] == "Project uses pytest via scripts/run_tests.sh."
    assert events[2]["old"] == "Project uses pytest via scripts/run_tests.sh."
    assert events[2]["new"] is None


def test_memory_restore_reverts_add_event(monkeypatch, tmp_path):
    monkeypatch.setenv("ARCEN_HOME", str(tmp_path))

    store = MemoryStore(memory_char_limit=500, user_char_limit=500)
    store.load_from_disk()
    assert store.add("memory", "Temporary remembered fact.")["success"]
    event_id = _events()[0]["id"]

    from arcen_cli.memory_setup import cmd_restore

    cmd_restore(SimpleNamespace(event_id=event_id, yes=True))

    assert MemoryStore._read_file(MemoryStore._path_for("memory")) == []
    events = _events()
    assert [event["action"] for event in events] == ["add", "restore"]
    assert events[-1]["actor"] == "user"
    assert events[-1]["metadata"]["restored_event_id"] == event_id


def test_memory_reset_records_restorable_snapshot(monkeypatch, tmp_path):
    monkeypatch.setenv("ARCEN_HOME", str(tmp_path))

    store = MemoryStore(memory_char_limit=500, user_char_limit=500)
    store.load_from_disk()
    assert store.add("memory", "Keep this recoverable.")["success"]

    from arcen_cli.memory_setup import cmd_reset, cmd_restore

    cmd_reset(SimpleNamespace(target="memory", yes=True))
    reset_event = _events()[-1]
    assert reset_event["action"] == "reset"
    assert reset_event["old"] == ["Keep this recoverable."]
    assert not MemoryStore._path_for("memory").exists()

    cmd_restore(SimpleNamespace(event_id=reset_event["id"], yes=True))

    assert MemoryStore._read_file(MemoryStore._path_for("memory")) == [
        "Keep this recoverable."
    ]
    assert _events()[-1]["action"] == "restore"
