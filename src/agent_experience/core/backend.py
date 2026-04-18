from enum import Enum


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
