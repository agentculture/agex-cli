import json
from datetime import datetime, timezone
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path

from agent_experience.core.backend import Backend
from agent_experience.core.config import load as load_config, save as save_config
from agent_experience.core.paths import ensure_init


def _fragments_file() -> Traversable:
    return files("agent_experience.commands.gamify").joinpath(
        "assets", "hooks", "claude-code.json"
    )


def _fragments_for(backend: Backend) -> list[dict]:
    if backend != Backend.CLAUDE_CODE:
        return []
    data = json.loads(_fragments_file().read_text(encoding="utf-8"))
    return data["fragments"]


def _hooks_file_for(backend: Backend, project_dir: Path) -> Path | None:
    if backend == Backend.CLAUDE_CODE:
        return project_dir / ".claude" / "hooks.json"
    return None


def _load_hooks_file(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(
            f"{path} is not valid JSON ({e}); refusing to overwrite. "
            "Fix or remove the file before re-running."
        )


def _write_hooks_file(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def install(backend: Backend) -> tuple[str, int, str]:
    ensure_init()
    project_dir = Path.cwd()
    hooks_file = _hooks_file_for(backend, project_dir)
    if hooks_file is None:
        return (_unsupported_notice(backend), 0, "")

    fragments = _fragments_for(backend)
    if not fragments:
        return (_unsupported_notice(backend), 0, "")

    try:
        hooks = _load_hooks_file(hooks_file)
    except ValueError as e:
        return ("", 2, f"agex: error: {e}")

    written_ids: list[str] = []
    for frag in fragments:
        event = frag["event"]
        entry = {"id": frag["id"], "hook": frag["hook"]}
        hooks.setdefault(event, [])
        if not any(e.get("id") == frag["id"] for e in hooks[event]):
            hooks[event].append(entry)
        written_ids.append(frag["id"])
    _write_hooks_file(hooks_file, hooks)

    cfg = load_config()
    previous = cfg.installed.get("gamify", {})
    if previous.get("hook_fragment_ids") != written_ids:
        cfg.installed["gamify"] = {
            "at": datetime.now(tz=timezone.utc).isoformat(),
            "hook_fragment_ids": written_ids,
        }
        save_config(cfg)

    lines = [
        f"# Gamify installed — {backend.value}",
        "",
        f"- Wrote {len(written_ids)} hook fragment(s) to `{hooks_file.relative_to(project_dir)}`.",
        "- Fragment IDs: " + ", ".join(f"`{i}`" for i in written_ids),
        "",
        f"Next: run `agex learn gamify --agent {backend.value}` to set up the levelup skill.",
        "",
    ]
    return ("\n".join(lines), 0, "")


def uninstall(backend: Backend) -> tuple[str, int, str]:
    ensure_init()
    project_dir = Path.cwd()
    hooks_file = _hooks_file_for(backend, project_dir)
    if hooks_file is None:
        return (_unsupported_notice(backend), 0, "")

    cfg = load_config()
    installed = cfg.installed.get("gamify", {})
    ids_to_remove = set(installed.get("hook_fragment_ids", []))
    if not ids_to_remove:
        return (f"# Gamify uninstalled — nothing to remove on {backend.value}.\n", 0, "")

    try:
        hooks = _load_hooks_file(hooks_file)
    except ValueError as e:
        return ("", 2, f"agex: error: {e}")

    for event in list(hooks.keys()):
        hooks[event] = [e for e in hooks[event] if e.get("id") not in ids_to_remove]
        if not hooks[event]:
            del hooks[event]
    _write_hooks_file(hooks_file, hooks)

    cfg.installed.pop("gamify", None)
    save_config(cfg)

    return (
        f"# Gamify uninstalled — removed {len(ids_to_remove)} fragment(s) from `{hooks_file.relative_to(project_dir)}`.\n",
        0,
        "",
    )


def _unsupported_notice(backend: Backend) -> str:
    return (
        f"## `gamify` is not supported on {backend.value}\n\n"
        f"Hooks are required to track usage events, and {backend.value} does not expose "
        f"a hook interface agex can write to.\n\n"
        "Want this supported? Open an issue: <https://github.com/OriNachum/agex/issues>\n"
    )
