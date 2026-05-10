"""Prioritized 'Next step:' rule keys for `agex pr` commands.

Each function takes the data the command already gathered and returns the
footer rule key + a context dict for variable substitution.  First match
wins.  Per-backend phrasing lives in `assets/backends/*.yaml`.
"""

from __future__ import annotations

from typing import Any


def lint_next_step(violations: list[Any], alignment_triggered: bool) -> tuple[str, dict[str, Any]]:
    if violations:
        return "lint_violations", {"violation_count": len(violations)}
    if alignment_triggered:
        return "lint_clean_with_alignment", {}
    return "lint_clean", {}


def open_next_step(pr: int, was_already_open: bool) -> tuple[str, dict[str, Any]]:
    key = "open_already_exists" if was_already_open else "open_recommend_read"
    return key, {"pr": pr}
