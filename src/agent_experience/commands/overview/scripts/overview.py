from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path

from agent_experience.backends.claude_code.probe import ProbeResult, probe as claude_code_probe
from agent_experience.core.backend import Backend
from agent_experience.core.paths import ensure_init
from agent_experience.core.render import render_string


_PROBES = {
    Backend.CLAUDE_CODE: claude_code_probe,
}


def _assets_root() -> Traversable:
    return files("agent_experience.commands.overview.assets")


def run(backend: Backend) -> tuple[str, int, str]:
    """Return (stdout, exit_code, stderr)."""
    ensure_init()
    project_dir = Path.cwd()

    if backend in _PROBES:
        probe_result = _PROBES[backend](project_dir)
    else:
        # Phase 8 will add probes for codex/copilot/acp. Until then, unknown
        # backends render as an empty snapshot (spec invariant 5: unsupported
        # is success). When Phase 8 lands, route through capabilities.py to
        # emit the unsupported-notice markdown instead.
        probe_result = ProbeResult()

    template_text = _assets_root().joinpath("sections.md.j2").read_text(encoding="utf-8")
    out = render_string(
        template_text,
        {"backend": backend.value, "project_dir": project_dir, "probe": probe_result},
    )
    return (out, 0, "")
