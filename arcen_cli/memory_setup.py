"""arcen memory setup|status — configure memory provider plugins.

Auto-detects installed memory providers via the plugin system.
Interactive curses-based UI for provider selection, then walks through
the provider's config schema. Writes config to config.yaml + .env.
"""

from __future__ import annotations

import difflib
import json
import os
import subprocess
import sys
import shlex
import tempfile
from pathlib import Path
from typing import Any

from arcen_constants import display_arcen_home, get_arcen_home
from arcen_cli.secret_prompt import masked_secret_prompt


# ---------------------------------------------------------------------------
# Curses-based interactive picker (same pattern as arcen tools)
# ---------------------------------------------------------------------------

def _curses_select(title: str, items: list[tuple[str, str]], default: int = 0) -> int:
    """Interactive single-select with arrow keys.

    items: list of (label, description) tuples.
    Returns selected index, or default on escape/quit.
    """
    from arcen_cli.curses_ui import curses_radiolist
    # Format (label, desc) tuples into display strings
    display_items = [
        f"{label}  {desc}" if desc else label
        for label, desc in items
    ]
    return curses_radiolist(title, display_items, selected=default, cancel_returns=default)


def _prompt(label: str, default: str | None = None, secret: bool = False) -> str:
    """Prompt for a value with optional default and secret masking."""
    suffix = f" [{default}]" if default else ""
    if secret:
        val = masked_secret_prompt(f"  {label}{suffix}: ")
    else:
        sys.stdout.write(f"  {label}{suffix}: ")
        sys.stdout.flush()
        val = sys.stdin.readline().strip()
    return val or (default or "")


# ---------------------------------------------------------------------------
# Provider discovery
# ---------------------------------------------------------------------------

def _install_dependencies(provider_name: str) -> None:
    """Install pip dependencies declared in plugin.yaml."""
    import subprocess
    from plugins.memory import find_provider_dir

    plugin_dir = find_provider_dir(provider_name)
    if not plugin_dir:
        return
    yaml_path = plugin_dir / "plugin.yaml"
    if not yaml_path.exists():
        return

    try:
        import yaml
        with open(yaml_path, encoding="utf-8") as f:
            meta = yaml.safe_load(f) or {}
    except Exception:
        return

    pip_deps = meta.get("pip_dependencies", [])
    if not pip_deps:
        return

    # pip name → import name mapping for packages where they differ
    _IMPORT_NAMES = {
        "honcho-ai": "honcho",
        "mem0ai": "mem0",
        "hindsight-client": "hindsight_client",
        "hindsight-all": "hindsight",
    }

    # Check which packages are missing
    missing = []
    for dep in pip_deps:
        import_name = _IMPORT_NAMES.get(dep, dep.replace("-", "_").split("[")[0])
        try:
            __import__(import_name)
        except ImportError:
            missing.append(dep)

    if not missing:
        return

    print(f"\n  Installing dependencies: {', '.join(missing)}")

    import shutil

    uv_path = shutil.which("uv")
    if uv_path:
        install_cmd = [uv_path, "pip", "install", "--python", sys.executable, "--quiet"] + missing
        manual_cmd = f"uv pip install --python {sys.executable} {' '.join(missing)}"
    else:
        pip_cmd = shutil.which("pip3") or shutil.which("pip")
        if not pip_cmd:
            print(f"  ⚠ uv not found — cannot install dependencies")
            print(f"  Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
            print(f"  Then re-run: arcen memory setup")
            return
        print(f"  ⚠ uv not found. Falling back to standard pip...")
        install_cmd = [sys.executable, "-m", "pip", "install", "--quiet"] + missing
        manual_cmd = f"{sys.executable} -m pip install {' '.join(missing)}"

    try:
        subprocess.run(
            install_cmd,
            check=True, timeout=120,
            capture_output=True,
        )
        print(f"  ✓ Installed {', '.join(missing)}")
    except subprocess.CalledProcessError as e:
        print(f"  ⚠ Failed to install {', '.join(missing)}")
        stderr = (e.stderr or b"").decode()[:200]
        if stderr:
            print(f"    {stderr}")
        print(f"  Run manually: {manual_cmd}")
    except Exception as e:
        print(f"  ⚠ Install failed: {e}")
        print(f"  Run manually: {manual_cmd}")

    # Also show external dependencies (non-pip) if any
    ext_deps = meta.get("external_dependencies", [])
    for dep in ext_deps:
        dep_name = dep.get("name", "")
        check_cmd = dep.get("check", "")
        install_cmd = dep.get("install", "")
        if check_cmd:
            try:
                subprocess.run(
                    shlex.split(check_cmd), check=True, capture_output=True, timeout=5
                )
            except Exception:
                if install_cmd:
                    print(f"\n  ⚠ '{dep_name}' not found. Install with:")
                    print(f"    {install_cmd}")


def _get_available_providers() -> list:
    """Discover memory providers from plugins/memory/.

    Returns list of (name, description, provider_instance) tuples.
    """
    try:
        from plugins.memory import discover_memory_providers, load_memory_provider
        raw = discover_memory_providers()
    except Exception:
        raw = []

    results = []
    for name, desc, available in raw:
        try:
            provider = load_memory_provider(name)
            if not provider:
                continue
        except Exception:
            continue

        schema = provider.get_config_schema() if hasattr(provider, "get_config_schema") else []
        has_secrets = any(f.get("secret") for f in schema)
        has_non_secrets = any(not f.get("secret") for f in schema)
        if has_secrets and has_non_secrets:
            setup_hint = "API key / local"
        elif has_secrets:
            setup_hint = "requires API key"
        elif not schema:
            setup_hint = "no setup needed"
        else:
            setup_hint = "local"

        results.append((name, setup_hint, provider))
    return results


# ---------------------------------------------------------------------------
# Built-in memory files: editor, audit history, restore
# ---------------------------------------------------------------------------

def _new_memory_store(*, history_actor: str = "agent", history_source: str = "memory_tool"):
    """Create a MemoryStore using configured built-in memory limits."""
    from arcen_cli.config import load_config
    from tools.memory_tool import MemoryStore

    config = load_config()
    mem_config = config.get("memory", {}) if isinstance(config.get("memory"), dict) else {}
    return MemoryStore(
        memory_char_limit=mem_config.get("memory_char_limit", 2200),
        user_char_limit=mem_config.get("user_char_limit", 1375),
        history_actor=history_actor,
        history_source=history_source,
    )


def _target_file(target: str) -> str:
    return "USER.md" if target == "user" else "MEMORY.md"


def _targets_from_arg(target: str) -> list[str]:
    if target == "all":
        return ["memory", "user"]
    return [target]


def _entry_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        from tools.memory_tool import ENTRY_DELIMITER

        return ENTRY_DELIMITER.join(str(v) for v in value)
    return str(value)


def _load_history_events() -> list[dict[str, Any]]:
    from tools.memory_tool import get_memory_history_path

    path = get_memory_history_path()
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def _find_history_event(event_id: str) -> dict[str, Any] | None:
    matches = [e for e in _load_history_events() if str(e.get("id", "")).startswith(event_id)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        print(f"  Event id prefix '{event_id}' is ambiguous. Use more characters.")
    return None


def _format_history_event(event: dict[str, Any]) -> str:
    eid = str(event.get("id", ""))[:12]
    ts = str(event.get("ts", ""))[:19]
    action = event.get("action", "?")
    target = event.get("target", "?")
    actor = event.get("actor", "?")
    new = _entry_text(event.get("new")).replace("\n", " ")
    old = _entry_text(event.get("old")).replace("\n", " ")
    preview = new or old
    if len(preview) > 80:
        preview = preview[:77] + "..."
    return f"{eid}  {ts}  {actor}:{action}:{target}  {preview}"


def _validate_entries(store, target: str, entries: list[str]) -> str | None:
    from tools.memory_tool import ENTRY_DELIMITER, _scan_memory_content

    cleaned = [str(e).strip() for e in entries if str(e).strip()]
    total = len(ENTRY_DELIMITER.join(cleaned)) if cleaned else 0
    limit = store._char_limit(target)
    if total > limit:
        return f"{target} memory would be {total:,}/{limit:,} chars. Shorten it first."
    for entry in cleaned:
        scan_error = _scan_memory_content(entry)
        if scan_error:
            return scan_error
    return None


def _write_entries_with_history(
    *,
    target: str,
    entries: list[str],
    action: str,
    old_entries: list[str],
    actor: str = "user",
    source: str = "memory_cli",
    metadata: dict[str, Any] | None = None,
) -> None:
    from tools.memory_tool import append_memory_history_event

    store = _new_memory_store(history_actor="user", history_source="memory_cli")
    cleaned = [str(e).strip() for e in entries if str(e).strip()]
    error = _validate_entries(store, target, cleaned)
    if error:
        raise ValueError(error)

    path = store._path_for(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    with store._file_lock(path):
        store._set_entries(target, cleaned)
        store.save_to_disk(target)
        append_memory_history_event(
            action=action,
            target=target,
            old_content=old_entries,
            new_content=cleaned,
            actor=actor,
            source=source,
            metadata=metadata,
        )


def cmd_list(args) -> None:
    """List built-in MEMORY.md / USER.md entries."""
    store = _new_memory_store()
    store.load_from_disk()
    target = getattr(args, "target", "all")

    for name in _targets_from_arg(target):
        entries = store._entries_for(name)
        current = store._char_count(name)
        limit = store._char_limit(name)
        print(f"\n{_target_file(name)} — {len(entries)} entries, {current:,}/{limit:,} chars")
        print("─" * 40)
        if not entries:
            print("  (empty)")
            continue
        for idx, entry in enumerate(entries, 1):
            print(f"{idx:>3}. {entry}")
    print()


def cmd_add(args) -> None:
    """Add a built-in memory entry from the CLI."""
    store = _new_memory_store(history_actor="user", history_source="memory_cli")
    store.load_from_disk()
    result = store.add(getattr(args, "target", "memory"), getattr(args, "content", ""))
    if result.get("success"):
        print(f"  ✓ {result.get('message', 'Entry added.')}")
        print(f"  Usage: {result.get('usage')}")
    else:
        print(f"  ✗ {result.get('error', 'Failed to add entry.')}")


def cmd_replace(args) -> None:
    """Replace a built-in memory entry from the CLI."""
    store = _new_memory_store(history_actor="user", history_source="memory_cli")
    store.load_from_disk()
    result = store.replace(
        getattr(args, "target", "memory"),
        getattr(args, "old_text", ""),
        getattr(args, "content", ""),
    )
    if result.get("success"):
        print(f"  ✓ {result.get('message', 'Entry replaced.')}")
        print(f"  Usage: {result.get('usage')}")
    else:
        print(f"  ✗ {result.get('error', 'Failed to replace entry.')}")


def cmd_remove(args) -> None:
    """Remove a built-in memory entry from the CLI."""
    store = _new_memory_store(history_actor="user", history_source="memory_cli")
    store.load_from_disk()
    result = store.remove(getattr(args, "target", "memory"), getattr(args, "old_text", ""))
    if result.get("success"):
        print(f"  ✓ {result.get('message', 'Entry removed.')}")
        print(f"  Usage: {result.get('usage')}")
    else:
        print(f"  ✗ {result.get('error', 'Failed to remove entry.')}")


def cmd_edit(args) -> None:
    """Open a built-in memory file in the user's editor with validation/history."""
    from tools.memory_tool import ENTRY_DELIMITER, MemoryStore

    target = getattr(args, "target", "memory")
    store = _new_memory_store()
    path = MemoryStore._path_for(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    old_entries = MemoryStore._read_file(path)
    initial = ENTRY_DELIMITER.join(old_entries)

    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
    if not editor:
        editor = "notepad" if os.name == "nt" else "vi"

    fd, tmp = tempfile.mkstemp(
        dir=str(path.parent),
        prefix=f".{_target_file(target)}.",
        suffix=".edit",
        text=True,
    )
    tmp_path = Path(tmp)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(initial)
            if initial and not initial.endswith("\n"):
                f.write("\n")

        code = subprocess.call(shlex.split(editor) + [str(tmp_path)])
        if code != 0:
            print(f"  Editor exited with status {code}; no memory changes saved.")
            return

        raw = tmp_path.read_text(encoding="utf-8")
        new_entries = [e.strip() for e in raw.split(ENTRY_DELIMITER) if e.strip()]
        if new_entries == old_entries:
            print("  No memory changes.")
            return

        _write_entries_with_history(
            target=target,
            entries=new_entries,
            action="edit",
            old_entries=old_entries,
        )
        print(f"  ✓ Saved {_target_file(target)}")
        print(f"  Entries: {len(old_entries)} → {len(new_entries)}")
    finally:
        try:
            tmp_path.unlink()
        except OSError:
            pass


def cmd_history(args) -> None:
    """Show built-in memory audit history."""
    events = _load_history_events()
    target = getattr(args, "target", "all")
    if target != "all":
        events = [e for e in events if e.get("target") == target]

    limit = max(1, int(getattr(args, "limit", 20)))
    events = events[-limit:]
    if getattr(args, "json", False):
        print(json.dumps(events, ensure_ascii=False, indent=2))
        return

    print("\nMemory history")
    print("─" * 40)
    if not events:
        print("  (no history yet)\n")
        return
    for event in events:
        print(f"  {_format_history_event(event)}")
    print()


def cmd_diff(args) -> None:
    """Show diffs for one memory history event or recent events."""
    event_id = getattr(args, "event_id", None)
    events = [_find_history_event(event_id)] if event_id else _load_history_events()[-max(1, int(getattr(args, "limit", 5))):]
    events = [e for e in events if e]
    if not events:
        print("  No matching memory history events.")
        return

    for event in events:
        before = _entry_text(event.get("old")).splitlines()
        after = _entry_text(event.get("new")).splitlines()
        print(f"\n{_format_history_event(event)}")
        print("─" * 40)
        diff = difflib.unified_diff(before, after, fromfile="before", tofile="after", lineterm="")
        shown = False
        for line in diff:
            print(line)
            shown = True
        if not shown:
            print("  (no textual diff)")
    print()


def cmd_restore(args) -> None:
    """Restore/revert a built-in memory history event."""
    event = _find_history_event(getattr(args, "event_id", ""))
    if not event:
        print("  No matching memory history event.")
        return

    target = event.get("target")
    if target not in {"memory", "user"}:
        print(f"  Cannot restore event target: {target!r}")
        return

    action = event.get("action")
    store = _new_memory_store()
    path = store._path_for(target)
    current = store._read_file(path)
    new_entries = list(current)

    if action == "add":
        added = str(event.get("new") or "").strip()
        if added in new_entries:
            new_entries.remove(added)
        else:
            print("  Added entry is no longer present; nothing to restore.")
            return
    elif action == "remove":
        removed = str(event.get("old") or "").strip()
        if removed and removed not in new_entries:
            new_entries.append(removed)
    elif action == "replace":
        old = str(event.get("old") or "").strip()
        new = str(event.get("new") or "").strip()
        if new in new_entries:
            new_entries[new_entries.index(new)] = old
        else:
            print("  Replacement entry is no longer present; refusing fuzzy restore.")
            return
    elif action in {"edit", "reset", "restore"}:
        old_entries = event.get("old")
        if not isinstance(old_entries, list):
            print(f"  Event {action!r} does not include a restorable snapshot.")
            return
        new_entries = [str(e) for e in old_entries if str(e).strip()]
    else:
        print(f"  Restore does not know how to revert action {action!r}.")
        return

    if new_entries == current:
        print("  Memory already matches the restored state.")
        return

    if not getattr(args, "yes", False):
        print(f"\n  Restore event {_format_history_event(event)}")
        print(f"  This will update {_target_file(target)}.")
        try:
            answer = input("  Type 'yes' to confirm: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n  Cancelled.\n")
            return
        if answer != "yes":
            print("  Cancelled.\n")
            return

    try:
        _write_entries_with_history(
            target=target,
            entries=new_entries,
            action="restore",
            old_entries=current,
            metadata={"restored_event_id": event.get("id"), "restored_action": action},
        )
    except ValueError as exc:
        print(f"  ✗ {exc}")
        return

    print(f"  ✓ Restored {_target_file(target)} from event {str(event.get('id'))[:12]}")


def cmd_reset(args) -> None:
    """Erase built-in memory with audit snapshots."""
    from tools.memory_tool import MemoryStore, append_memory_history_event

    mem_dir = get_arcen_home() / "memories"
    target = getattr(args, "target", "all")
    targets = _targets_from_arg(target)
    existing = []
    for name in targets:
        path = MemoryStore._path_for(name)
        if path.exists():
            existing.append((name, path, _target_file(name), MemoryStore._read_file(path)))

    if not existing:
        print(f"\n  Nothing to reset — no memory files found in {display_arcen_home()}/memories/\n")
        return

    print("\n  This will erase the following built-in memory files:")
    for _name, path, filename, entries in existing:
        size = path.stat().st_size
        print(f"    - {filename} — {len(entries)} entries, {size:,} bytes")

    if not getattr(args, "yes", False):
        try:
            answer = input("\n  Type 'yes' to confirm: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n  Cancelled.\n")
            return
        if answer != "yes":
            print("  Cancelled.\n")
            return

    mem_dir.mkdir(parents=True, exist_ok=True)
    for name, path, filename, entries in existing:
        path.unlink()
        append_memory_history_event(
            action="reset",
            target=name,
            old_content=entries,
            new_content=[],
            actor="user",
            source="memory_cli",
        )
        print(f"  ✓ Deleted {filename}")

    print(f"\n  Memory reset complete. Restore is available via `arcen memory history` + `arcen memory restore <event-id>`.")
    print(f"  Files were in: {display_arcen_home()}/memories/\n")


# ---------------------------------------------------------------------------
# Setup wizard
# ---------------------------------------------------------------------------

def cmd_setup_provider(provider_name: str) -> None:
    """Run memory setup for a specific provider, skipping the picker."""
    from arcen_cli.config import load_config, save_config

    providers = _get_available_providers()
    match = None
    for name, desc, provider in providers:
        if name == provider_name:
            match = (name, desc, provider)
            break

    if not match:
        print(f"\n  Memory provider '{provider_name}' not found.")
        print("  Run 'arcen memory setup' to see available providers.\n")
        return

    name, _, provider = match

    _install_dependencies(name)

    config = load_config()
    if not isinstance(config.get("memory"), dict):
        config["memory"] = {}

    if hasattr(provider, "post_setup"):
        arcen_home = str(get_arcen_home())
        provider.post_setup(arcen_home, config)
        return

    # Fallback: generic schema-based setup (same as cmd_setup)
    config["memory"]["provider"] = name
    save_config(config)
    print(f"\n  Memory provider: {name}")
    print(f"  Activation saved to config.yaml\n")


def cmd_setup(args) -> None:
    """Interactive memory provider setup wizard."""
    from arcen_cli.config import load_config, save_config

    providers = _get_available_providers()

    if not providers:
        print("\n  No memory provider plugins detected.")
        print("  Install a plugin to ~/.arcen/plugins/ and try again.\n")
        return

    # Build picker items
    items = []
    for name, desc, _ in providers:
        items.append((name, f"— {desc}"))
    items.append(("Built-in only", "— MEMORY.md / USER.md (default)"))

    builtin_idx = len(items) - 1
    selected = _curses_select("Memory provider setup", items, default=builtin_idx)

    config = load_config()
    if not isinstance(config.get("memory"), dict):
        config["memory"] = {}

    # Built-in only
    if selected >= len(providers) or selected < 0:
        config["memory"]["provider"] = ""
        save_config(config)
        print("\n  ✓ Memory provider: built-in only")
        print("  Saved to config.yaml\n")
        return

    name, _, provider = providers[selected]

    # Install pip dependencies if declared in plugin.yaml
    _install_dependencies(name)

    # If the provider has a post_setup hook, delegate entirely to it.
    # The hook handles its own config, connection test, and activation.
    if hasattr(provider, "post_setup"):
        arcen_home = str(get_arcen_home())
        provider.post_setup(arcen_home, config)
        return

    schema = provider.get_config_schema() if hasattr(provider, "get_config_schema") else []

    provider_config = config["memory"].get(name, {})
    if not isinstance(provider_config, dict):
        provider_config = {}

    env_path = get_arcen_home() / ".env"
    env_writes = {}

    if schema:
        print(f"\n  Configuring {name}:\n")

        for field in schema:
            key = field["key"]
            desc = field.get("description", key)
            default = field.get("default")
            # Dynamic default: look up default from another field's value
            default_from = field.get("default_from")
            if default_from and isinstance(default_from, dict):
                ref_field = default_from.get("field", "")
                ref_map = default_from.get("map", {})
                ref_value = provider_config.get(ref_field, "")
                if ref_value and ref_value in ref_map:
                    default = ref_map[ref_value]
            is_secret = field.get("secret", False)
            choices = field.get("choices")
            env_var = field.get("env_var")
            url = field.get("url")

            # Skip fields whose "when" condition doesn't match
            when = field.get("when")
            if when and isinstance(when, dict):
                if not all(provider_config.get(k) == v for k, v in when.items()):
                    continue

            if choices and not is_secret:
                # Use curses picker for choice fields
                choice_items = [(c, "") for c in choices]
                current = provider_config.get(key, default)
                current_idx = 0
                if current and current in choices:
                    current_idx = choices.index(current)
                sel = _curses_select(f"  {desc}", choice_items, default=current_idx)
                provider_config[key] = choices[sel]
            elif is_secret:
                # Prompt for secret
                existing = os.environ.get(env_var, "") if env_var else ""
                if existing:
                    masked = f"...{existing[-4:]}" if len(existing) > 4 else "set"
                    val = _prompt(f"{desc} (current: {masked}, blank to keep)", secret=True)
                else:
                    hint = f"  Get yours at {url}" if url else ""
                    if hint:
                        print(hint)
                    val = _prompt(desc, secret=True)
                if val and env_var:
                    env_writes[env_var] = val
            else:
                # Regular text prompt
                current = provider_config.get(key)
                effective_default = current or default
                val = _prompt(desc, default=str(effective_default) if effective_default else None)
                if val:
                    provider_config[key] = val
                    # Also write to .env if this field has an env_var
                    if env_var and env_var not in env_writes:
                        env_writes[env_var] = val

    # Write activation key to config.yaml
    config["memory"]["provider"] = name
    save_config(config)

    # Write non-secret config to provider's native location
    arcen_home = str(get_arcen_home())
    if provider_config and hasattr(provider, "save_config"):
        try:
            provider.save_config(provider_config, arcen_home)
        except Exception as e:
            print(f"  Failed to write provider config: {e}")

    # Write secrets to .env
    if env_writes:
        _write_env_vars(env_path, env_writes)

    print(f"\n  Memory provider: {name}")
    print(f"  Activation saved to config.yaml")
    if provider_config:
        print(f"  Provider config saved")
    if env_writes:
        print(f"  API keys saved to .env")
    print(f"\n  Start a new session to activate.\n")


def _write_env_vars(env_path: Path, env_writes: dict) -> None:
    """Append or update env vars in .env file."""
    env_path.parent.mkdir(parents=True, exist_ok=True)

    existing_lines = []
    if env_path.exists():
        existing_lines = env_path.read_text(encoding="utf-8").splitlines()

    updated_keys = set()
    new_lines = []
    for line in existing_lines:
        key_match = line.split("=", 1)[0].strip() if "=" in line else ""
        if key_match in env_writes:
            new_lines.append(f"{key_match}={env_writes[key_match]}")
            updated_keys.add(key_match)
        else:
            new_lines.append(line)

    for key, val in env_writes.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={val}")

    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    # Restrict permissions — .env holds API keys and tokens.
    try:
        import stat
        env_path.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 0600
    except OSError:
        pass  # Windows or read-only FS


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

def cmd_status(args) -> None:
    """Show current memory provider config."""
    from arcen_cli.config import load_config

    config = load_config()
    mem_config = config.get("memory", {})
    provider_name = mem_config.get("provider", "")

    print(f"\nMemory status\n" + "─" * 40)
    print(f"  Built-in:  always active")
    print(f"  Provider:  {provider_name or '(none — built-in only)'}")

    if provider_name:
        provider_config = mem_config.get(provider_name, {})
        if provider_config:
            print(f"\n  {provider_name} config:")
            for key, val in provider_config.items():
                print(f"    {key}: {val}")

        providers = _get_available_providers()
        found = any(name == provider_name for name, _, _ in providers)
        if found:
            print(f"\n  Plugin:    installed ✓")
            for pname, _, p in providers:
                if pname == provider_name:
                    if p.is_available():
                        print(f"  Status:    available ✓")
                    else:
                        print(f"  Status:    not available ✗")
                        schema = p.get_config_schema() if hasattr(p, "get_config_schema") else []
                        # Check all fields that have env_var (both secret and non-secret)
                        required_fields = [f for f in schema if f.get("env_var")]
                        if required_fields:
                            print(f"  Missing:")
                            for f in required_fields:
                                env_var = f.get("env_var", "")
                                url = f.get("url", "")
                                is_set = bool(os.environ.get(env_var))
                                mark = "✓" if is_set else "✗"
                                line = f"    {mark} {env_var}"
                                if url and not is_set:
                                    line += f"  → {url}"
                                print(line)
                    break
        else:
            print(f"\n  Plugin:    NOT installed ✗")
            print(f"  Install the '{provider_name}' memory plugin to ~/.arcen/plugins/")

    providers = _get_available_providers()
    if providers:
        print(f"\n  Installed plugins:")
        for pname, desc, _ in providers:
            active = " ← active" if pname == provider_name else ""
            print(f"    • {pname}  ({desc}){active}")

    print()


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

def memory_command(args) -> None:
    """Route memory subcommands."""
    sub = getattr(args, "memory_command", None)
    if sub == "setup":
        provider = getattr(args, "provider", None)
        if provider:
            cmd_setup_provider(provider)
        else:
            cmd_setup(args)
    elif sub == "status":
        cmd_status(args)
    elif sub == "list":
        cmd_list(args)
    elif sub == "add":
        cmd_add(args)
    elif sub == "replace":
        cmd_replace(args)
    elif sub == "remove":
        cmd_remove(args)
    elif sub == "edit":
        cmd_edit(args)
    elif sub == "history":
        cmd_history(args)
    elif sub == "diff":
        cmd_diff(args)
    elif sub == "restore":
        cmd_restore(args)
    elif sub == "reset":
        cmd_reset(args)
    else:
        cmd_status(args)
