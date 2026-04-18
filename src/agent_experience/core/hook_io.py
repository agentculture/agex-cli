import json
import os
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
    path = _stream_path(stream)
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def render_table(events: list[dict[str, Any]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    rows = ["| " + " | ".join(str(e.get(c, "")) for c in columns) + " |" for e in events]
    return "\n".join([header, sep, *rows]) + "\n"
