from enum import Enum
from pathlib import Path

import yaml


class Backend(str, Enum):
    CLAUDE_CODE = "claude-code"
    CODEX = "codex"
    COPILOT = "copilot"
    ACP = "acp"


def parse_backend(value: str) -> Backend:
    try:
        return Backend(value)
    except ValueError:
        valid = ", ".join(b.value for b in Backend)
        raise ValueError(f"unknown backend '{value}' (one of: {valid})") from None


def resolve_backend(arg: str | None, project_dir: Path) -> Backend:
    """Resolve --agent: explicit arg wins, else first agent's backend
    in culture.yaml, else raise.
    """
    if arg is not None:
        return parse_backend(arg)
    culture = project_dir / "culture.yaml"
    if culture.exists():
        try:
            data = yaml.safe_load(culture.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            data = {}
        agents = data.get("agents") or []
        if agents and isinstance(agents[0], dict):
            backend_value = agents[0].get("backend")
            if backend_value:
                return parse_backend(backend_value)
    valid = ", ".join(b.value for b in Backend)
    raise ValueError(
        f"--agent required (one of: {valid}) or set 'backend:' on the "
        f"first agent in culture.yaml"
    )
