"""Shared readiness / thread-resolution helpers for the `pr` namespace.

Used by both `pr read --wait` and `pr await`.
"""

from __future__ import annotations

from typing import Any

from agent_experience.core import config as cfg_mod

DEFAULT_REVIEWERS = ["qodo"]
POLL_INTERVAL_SEC = 60


def required_reviewers() -> list[str]:
    try:
        cfg = cfg_mod.load()
    except Exception:
        return list(DEFAULT_REVIEWERS)
    return list(cfg.pr.get("required_reviewers", DEFAULT_REVIEWERS))


def is_ready(
    comments: list[dict[str, Any]], required: list[str]
) -> tuple[bool, list[str]]:
    """Return (ready, still_waiting). Ready = each required reviewer has at
    least one inline OR review comment with non-trivial body."""
    seen: set[str] = set()
    for c in comments:
        raw_author = (c.get("author") or "").lower()
        author = raw_author.removesuffix("[bot]").removesuffix("[")
        body = (c.get("body") or "").strip()
        if not body:
            continue
        for r in required:
            if r.lower() in author:
                seen.add(r)
    waiting = [r for r in required if r not in seen]
    return (not waiting, waiting)


def threads_unresolved(comments: list[dict[str, Any]]) -> int:
    """Inline comments with no in_reply_to that haven't been answered.
    v0.1 heuristic: count distinct top-level inline comments."""
    inline = [c for c in comments if c.get("type") == "inline"]
    top_level = [c for c in inline if c.get("in_reply_to") is None]
    return max(0, len(top_level))
