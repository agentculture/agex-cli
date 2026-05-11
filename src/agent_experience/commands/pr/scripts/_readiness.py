"""Shared readiness / thread-resolution helpers for the `pr` namespace.

Used by both `pr read --wait` and `pr await`.
"""

from __future__ import annotations

from typing import Any

from agent_experience.core import config as cfg_mod
from agent_experience.core import github

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


def threads_unresolved(pr: int) -> int:
    """Count of review threads on ``pr`` whose ``isResolved`` flag is false.

    Queries GitHub's GraphQL reviewThreads endpoint so threads resolved
    via ``resolveReviewThread`` (what ``pr reply`` does) are excluded
    from the count.  Returns 0 on any query failure so the caller stays
    safe on PRs without review threads.
    """
    try:
        threads = github.pr_review_threads(pr)
    except RuntimeError:
        return 0
    return sum(1 for t in threads if not t.get("isResolved"))
