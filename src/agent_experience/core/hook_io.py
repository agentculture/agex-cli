import json
import os
import warnings
from pathlib import Path
from typing import Any

import portalocker

from agent_experience.core.paths import data_dir


def _stream_path(stream: str) -> Path:
    return data_dir() / f"{stream}.json"


def append_event(stream: str, payload: dict[str, Any]) -> None:
    path = _stream_path(stream)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(payload, separators=(",", ":")) + "\n"
    with path.open("a", encoding="utf-8") as fh:
        portalocker.lock(fh, portalocker.LOCK_EX)
        try:
            fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())
        finally:
            portalocker.unlock(fh)


def load_events(stream: str) -> list[dict[str, Any]]:
    # Malformed lines (partial writes, external edits) are skipped with a
    # warning rather than raised, so `agex hook read` stays a read-only
    # snapshot even when a `.agex/data/*.json` file gets corrupted.
    path = _stream_path(stream)
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as e:
            warnings.warn(
                f"{path}:{lineno}: skipping malformed JSON line: {e}", stacklevel=2
            )
    return events


def render_table(events: list[dict[str, Any]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    rows = ["| " + " | ".join(str(e.get(c, "")) for c in columns) + " |" for e in events]
    return "\n".join([header, sep, *rows]) + "\n"
