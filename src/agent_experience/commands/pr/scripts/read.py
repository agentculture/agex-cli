"""`agex pr read` — unified PR briefing.

v0.1: one-shot read.  Task 17 adds --wait + readiness loop.
"""

from __future__ import annotations

import subprocess
import sys
import time
from importlib.resources import files
from pathlib import Path
from typing import Any

from agent_experience.commands.pr.assets.rules.next_step_rules import (
    read_next_step,
    read_wait_timeout_step,
)
from agent_experience.commands.pr.scripts import _journal
from agent_experience.commands.pr.scripts._footer import render_footer
from agent_experience.core import config as cfg_mod
from agent_experience.core import github
from agent_experience.core.backend import resolve_backend
from agent_experience.core.render import render_string

_TEMPLATES_PKG = "agent_experience.commands.pr.assets.templates"

_DEFAULT_REVIEWERS = ["qodo"]
_POLL_INTERVAL_SEC = 60


def _resolve_pr(pr: int | None) -> int:
    if pr is not None:
        return pr
    view = github.pr_view(None)
    if view is None:
        raise ValueError("no PR found for current branch; pass <PR> explicitly")
    return int(view["number"])


def _project_key() -> str:
    """SonarCloud project key convention: <owner>_<repo>."""
    slug = github._repo_slug()  # noqa: SLF001
    return slug.replace("/", "_")


def _has_recent_local_commits(journal_events: list[dict[str, Any]], pr: int) -> bool:
    """True if `git log` shows commits authored after the most recent
    `pr_read` event for this PR.  No event yet → False (first read)."""
    last_read = next(
        (e for e in reversed(journal_events) if e.get("type") == "pr_read" and e.get("pr") == pr),
        None,
    )
    if last_read is None:
        return False
    ts = last_read["ts"]
    out = subprocess.run(
        ["git", "log", f"--since={ts}", "--pretty=%H"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    return bool(out)


def _threads_unresolved(comments: list[dict[str, Any]]) -> int:
    """Inline comments with no in_reply_to that haven't been answered.
    v0.1 heuristic: count distinct top-level inline comments (no in_reply_to).
    Refined in a follow-up.
    """
    inline = [c for c in comments if c.get("type") == "inline"]
    top_level = [c for c in inline if c.get("in_reply_to") is None]
    return max(0, len(top_level))


def _required_reviewers() -> list[str]:
    try:
        cfg = cfg_mod.load()
    except Exception:
        return list(_DEFAULT_REVIEWERS)
    return list(cfg.pr.get("required_reviewers", _DEFAULT_REVIEWERS))


def _is_ready(comments: list[dict[str, Any]], required: list[str]) -> tuple[bool, list[str]]:
    """Return (ready, still_waiting). Ready = each required reviewer has at
    least one inline OR review comment with non-trivial body."""
    seen: set[str] = set()
    for c in comments:
        raw_author = (c.get("author") or "").lower()
        # Strip common bot suffixes like "[bot]" before matching.
        author = raw_author.removesuffix("[bot]").removesuffix("[")
        body = (c.get("body") or "").strip()
        if not body:
            continue
        for r in required:
            if r.lower() in author:
                seen.add(r)
    waiting = [r for r in required if r not in seen]
    return (not waiting, waiting)


def run(
    agent: str | None,
    project_dir: Path,
    pr: int | None,
    wait: int | None,
) -> tuple[str, int, str]:
    backend = resolve_backend(agent, project_dir)
    pr_number = _resolve_pr(pr)

    waited_secs = 0
    waiting_for: list[str] = []
    if wait is not None and wait > 0:
        required = _required_reviewers()
        deadline = wait
        ready = False
        while waited_secs < deadline:
            comments = github.pr_comments(pr_number)
            ready, waiting_for = _is_ready(comments, required)
            sys.stderr.write(
                f"agex: pr_read --wait: pr={pr_number} waited={waited_secs}s "
                f"ready={ready} waiting_for={waiting_for}\n"
            )
            sys.stderr.flush()
            if ready:
                _journal.append(
                    {"type": "readiness_arrived", "pr": pr_number, "waited_secs": waited_secs}
                )
                break
            interval = min(_POLL_INTERVAL_SEC, max(1, deadline - waited_secs))
            time.sleep(interval)
            waited_secs += interval
        if not ready:
            # Timeout — render still-waiting briefing.
            pr_meta = github.pr_view(str(pr_number))
            checks = github.pr_checks(pr_number)
            comments = github.pr_comments(pr_number)
            footer_key, footer_ctx = read_wait_timeout_step(pr_number, waiting_for)
            footer = render_footer(footer_key, backend, footer_ctx)
            template = (
                files(_TEMPLATES_PKG).joinpath("pr_briefing.md.j2").read_text(encoding="utf-8")
            )
            stdout = render_string(
                template,
                {
                    "pr": pr_number,
                    "pr_meta": pr_meta,
                    "checks": checks,
                    "comments": comments,
                    "sonar_gate": None,
                    "sonar_issues": [],
                    "waiting_for": waiting_for,
                    "footer": footer,
                },
            )
            return stdout, 0, ""

    # Either no --wait, or readiness arrived: full briefing path.
    pr_meta = github.pr_view(str(pr_number))
    checks = github.pr_checks(pr_number)
    comments = github.pr_comments(pr_number)
    project_key = _project_key()
    sonar_gate = github.sonar_quality_gate(project_key, pr_number)
    sonar_issues = github.sonar_new_issues(project_key, pr_number)

    threads_unresolved = _threads_unresolved(comments)
    journal_events = _journal.load()
    has_recent_commits = _has_recent_local_commits(journal_events, pr_number)
    ci_red = any(c.get("conclusion") == "failure" for c in checks)

    _journal.append(
        {
            "type": "pr_read",
            "pr": pr_number,
            "comment_count": len(comments),
            "threads_unresolved": threads_unresolved,
            "ci_state": "failure" if ci_red else "ok",
        }
    )

    footer_key, footer_ctx = read_next_step(
        pr=pr_number,
        threads_unresolved=threads_unresolved,
        has_recent_local_commits=has_recent_commits,
        ci_red=ci_red,
    )
    footer = render_footer(footer_key, backend, footer_ctx)

    template = files(_TEMPLATES_PKG).joinpath("pr_briefing.md.j2").read_text(encoding="utf-8")
    stdout = render_string(
        template,
        {
            "pr": pr_number,
            "pr_meta": pr_meta,
            "checks": checks,
            "comments": comments,
            "sonar_gate": sonar_gate,
            "sonar_issues": sonar_issues,
            "waiting_for": [],
            "footer": footer,
        },
    )
    return stdout, 0, ""
