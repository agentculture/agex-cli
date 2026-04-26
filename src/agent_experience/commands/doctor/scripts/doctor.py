"""`agex doctor` — read-only health check.

Composes a list of per-check `CheckResult` rows grouped into categories, then
renders them through the Jinja report template.  No side effects: never calls
``ensure_init`` or touches the filesystem outside of read attempts.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from importlib.resources import as_file, files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Literal

import yaml

from agent_experience import __version__
from agent_experience.core.paths import (
    GITIGNORE_CONTENT,
    agex_dir,
    config_path,
    data_dir,
)
from agent_experience.core.render import render_string
from agent_experience.core.skill_loader import load_skill

Status = Literal["ok", "warn", "fail", "info"]
_ROLE_RE = re.compile(r"^[a-z][a-z0-9-]*$")
_MIN_PYTHON = (3, 10)


@dataclass
class CheckResult:
    name: str
    status: Status
    detail: str


@dataclass
class Category:
    title: str
    results: list[CheckResult] = field(default_factory=list)


def _commands_root() -> Traversable:
    return files("agent_experience.commands")


def _doctor_assets() -> Traversable:
    return files("agent_experience.commands").joinpath("doctor", "assets")


# --- Install checks --------------------------------------------------------


def _check_version() -> CheckResult:
    if not __version__ or __version__ == "unknown":
        return CheckResult(
            "agex version",
            "fail",
            "Could not resolve `agent_experience.__version__`. Reinstall with "
            "`uv pip install -e .[dev]` or `pipx install agex-cli`.",
        )
    return CheckResult("agex version", "ok", __version__)


def _check_python() -> CheckResult:
    cur = sys.version_info[:3]
    detail = ".".join(str(p) for p in cur)
    if cur[:2] < _MIN_PYTHON:
        return CheckResult(
            "Python",
            "fail",
            f"{detail} (need >= {_MIN_PYTHON[0]}.{_MIN_PYTHON[1]})",
        )
    return CheckResult("Python", "ok", detail)


def _check_resources() -> CheckResult:
    try:
        # If hatch packaging is broken, this raises or returns an empty
        # traversable. Probe a known-shipped file to be sure.
        agex_md = _commands_root().joinpath("explain", "assets", "topics", "agex.md")
        if not agex_md.is_file():
            return CheckResult(
                "Package resources",
                "fail",
                "Cannot locate `commands/explain/assets/topics/agex.md`. " "Reinstall the package.",
            )
    except Exception as exc:  # pragma: no cover - defensive only
        return CheckResult("Package resources", "fail", f"resource lookup raised: {exc}")
    return CheckResult("Package resources", "ok", "all shipped assets reachable")


# --- Project state checks --------------------------------------------------


def _check_agex_dir() -> CheckResult:
    root = agex_dir()
    if not root.exists():
        return CheckResult(
            "`.agex/` directory",
            "info",
            f"not initialized at `{root}` — run any backend-aware command "
            "(e.g. `agex overview --agent claude-code`) to bootstrap.",
        )
    if not root.is_dir():
        return CheckResult(
            "`.agex/` directory",
            "fail",
            f"`{root}` exists but is not a directory.",
        )
    return CheckResult("`.agex/` directory", "ok", str(root))


def _check_config_toml() -> CheckResult:
    path = config_path()
    if not path.exists():
        return CheckResult(
            "`.agex/config.toml`",
            "info",
            "not present (expected when `.agex/` is uninitialized).",
        )

    # Parse defensively — config.load() raises on malformed TOML, which we
    # catch and surface as a fail row rather than letting bubble up.
    try:
        from agent_experience.core import config as config_module

        cfg = config_module.load()
    except Exception as exc:
        return CheckResult(
            "`.agex/config.toml`",
            "fail",
            f"failed to parse: {exc}. Edit or delete the file.",
        )

    if cfg.agex_version and cfg.agex_version != __version__:
        return CheckResult(
            "`.agex/config.toml`",
            "warn",
            (
                f'`agex_version = "{cfg.agex_version}"` does not match installed '
                f"`{__version__}`. Will reconcile on next write."
            ),
        )
    return CheckResult("`.agex/config.toml`", "ok", f"version {cfg.agex_version}")


def _check_gitignore() -> CheckResult:
    root = agex_dir()
    gi = root / ".gitignore"
    if not root.exists():
        return CheckResult("`.agex/.gitignore`", "info", "skipped (no `.agex/`).")
    if not gi.exists():
        return CheckResult(
            "`.agex/.gitignore`",
            "warn",
            "missing — `data/` may end up tracked. Re-run any agex command to restore.",
        )
    actual = gi.read_text(encoding="utf-8")
    if actual != GITIGNORE_CONTENT:
        return CheckResult(
            "`.agex/.gitignore`",
            "warn",
            "content drifted from the managed default — `data/` may not be ignored.",
        )
    return CheckResult("`.agex/.gitignore`", "ok", "matches managed content")


def _check_data_dir() -> CheckResult:
    if not agex_dir().exists():
        return CheckResult("`.agex/data/`", "info", "skipped (no `.agex/`).")
    d = data_dir()
    if not d.exists():
        return CheckResult(
            "`.agex/data/`",
            "warn",
            f"`{d}` is missing — re-run any agex command to recreate it.",
        )
    if not d.is_dir():
        return CheckResult("`.agex/data/`", "fail", f"`{d}` is not a directory.")
    # Read-only contract — no probe write. Just check perms.
    import os

    if not os.access(d, os.W_OK):
        return CheckResult("`.agex/data/`", "fail", f"`{d}` is not writable.")
    return CheckResult("`.agex/data/`", "ok", str(d))


# --- Internal consistency checks -------------------------------------------


def _iter_skill_relpaths() -> list[str]:
    with as_file(_commands_root()) as root:
        return sorted("/".join(p.relative_to(root).parts) for p in root.glob("**/SKILL.md"))


def _check_skill_md_consistency() -> CheckResult:
    relpaths = _iter_skill_relpaths()
    if not relpaths:
        return CheckResult(
            "Shipped SKILL.md frontmatter",
            "fail",
            "No SKILL.md files discovered — package data is missing.",
        )
    failures: list[str] = []
    with as_file(_commands_root()) as root:
        for rel in relpaths:
            try:
                load_skill(root / rel)
            except Exception as exc:
                failures.append(f"{rel}: {exc}")
    if failures:
        return CheckResult(
            "Shipped SKILL.md frontmatter",
            "fail",
            f"{len(failures)} of {len(relpaths)} failed: {'; '.join(failures)}",
        )
    return CheckResult(
        "Shipped SKILL.md frontmatter",
        "ok",
        f"{len(relpaths)} files parse cleanly",
    )


def _check_capability_yaml() -> CheckResult:
    failures: list[str] = []
    count = 0
    with as_file(_commands_root()) as root:
        for path in root.glob("**/assets/backends/*.yaml"):
            count += 1
            try:
                yaml.safe_load(path.read_text(encoding="utf-8"))
            except Exception as exc:
                failures.append(f"{path.relative_to(root)}: {exc}")
    if failures:
        return CheckResult(
            "Backend capability YAML",
            "fail",
            f"{len(failures)} of {count} failed: {'; '.join(failures)}",
        )
    if count == 0:
        return CheckResult(
            "Backend capability YAML",
            "info",
            "no per-backend YAML files found (expected once `overview` ships).",
        )
    return CheckResult("Backend capability YAML", "ok", f"{count} files parse cleanly")


# --- Operator verification (markdown-only, no programmatic check) ----------


_OPERATOR_CHECKLIST = [
    "Confirm `.agex/config.toml` is committed and `.agex/data/` is gitignored.",
    "Confirm your shell tool can invoke `agex --version` and `agex doctor`.",
    "If you installed hooks via `agex gamify`, confirm the backend hook file "
    "still contains the `agex:` fragment IDs recorded in `.agex/config.toml`.",
]


# --- Role section ----------------------------------------------------------


def _resolve_role(role: str) -> Traversable | None:
    if not _ROLE_RE.match(role):
        return None
    candidate = _doctor_assets().joinpath("roles", f"{role}.md.j2")
    return candidate if candidate.is_file() else None


# --- Aggregation -----------------------------------------------------------


def _build_categories() -> list[Category]:
    return [
        Category(
            "Install",
            [_check_version(), _check_python(), _check_resources()],
        ),
        Category(
            "Project state",
            [
                _check_agex_dir(),
                _check_config_toml(),
                _check_gitignore(),
                _check_data_dir(),
            ],
        ),
        Category(
            "Internal consistency",
            [_check_skill_md_consistency(), _check_capability_yaml()],
        ),
    ]


def _summarize(categories: list[Category]) -> dict[str, int]:
    summary = {"ok": 0, "warn": 0, "fail": 0, "info": 0}
    for cat in categories:
        for r in cat.results:
            summary[r.status] += 1
    return summary


def run(role: str | None = None) -> tuple[str, int, str]:
    """Return ``(stdout, exit_code, stderr)``.

    Read-only.  Never initializes ``.agex/``.
    """
    if role is not None and _ROLE_RE.match(role) is None:
        return ("", 2, f"agex: error: invalid role slug '{role}'")

    role_section: str | None = None
    if role is not None:
        trav = _resolve_role(role)
        if trav is None:
            return ("", 2, f"agex: error: unknown role '{role}'")
        role_section = trav.read_text(encoding="utf-8")

    categories = _build_categories()
    summary = _summarize(categories)

    template_text = _doctor_assets().joinpath("report.md.j2").read_text(encoding="utf-8")
    out = render_string(
        template_text,
        {
            "version": __version__,
            "project_dir": str(Path.cwd()),
            "categories": categories,
            "operator_checklist": _OPERATOR_CHECKLIST,
            "role": role,
            "role_section": role_section,
            "summary": summary,
        },
    )

    if summary["fail"] > 0:
        stderr = f"agex: error: {summary['fail']} health check(s) failed"
        return (out, 1, stderr)
    return (out, 0, "")
