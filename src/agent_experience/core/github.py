"""Thin wrapper around the `gh` CLI for the `agex pr` namespace.

Every call shells `gh ...` and parses JSON.  Hard failures raise
``RuntimeError`` with the gh stderr first line; soft failures
(missing SonarCloud project, missing PR for branch) return ``None``
or ``[]`` so renders still succeed.

When the future zero-trust httpx swap lands, only this module changes.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml


def _run_gh(args: list[str], stdin: str | None = None) -> str:
    """Shell out to `gh <args>` and return stdout.

    Raises RuntimeError(f"gh failed: {first_stderr_line}") on non-zero exit.
    """
    result = subprocess.run(  # nosec B603 - args are constructed from typed callers
        ["gh", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        first = (result.stderr or "").splitlines()[0] if result.stderr else "no stderr"
        raise RuntimeError(f"gh failed: {first}")
    return result.stdout


_PR_URL_RE = re.compile(r"/pull/(\d+)")
_PR_VIEW_FIELDS = "number,state,title,url,headRefName,baseRefName,isDraft"


def resolve_nick(project_dir: Path) -> str:
    """Return the agent's nick: first agent's `suffix` in culture.yaml,
    or the project_dir basename if no usable nick is found.
    """
    culture = project_dir / "culture.yaml"
    if culture.exists():
        try:
            data = yaml.safe_load(culture.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            data = {}
        agents = data.get("agents") or []
        if agents and isinstance(agents[0], dict):
            suffix = agents[0].get("suffix")
            if suffix:
                return str(suffix)
    return project_dir.name


def pr_create(title: str, body: str, draft: bool) -> int:
    """Create a PR via `gh pr create`; return the new PR number."""
    args = ["pr", "create", "--title", title, "--body", body]
    if draft:
        args.append("--draft")
    stdout = _run_gh(args)
    match = _PR_URL_RE.search(stdout)
    if not match:
        raise RuntimeError(f"gh pr create succeeded but URL not found in: {stdout!r}")
    return int(match.group(1))


def pr_view(pr_or_branch: str | None) -> dict[str, Any] | None:
    """Return the gh-pr-view dict, or None if no PR exists for the branch."""
    args = ["pr", "view", "--json", _PR_VIEW_FIELDS]
    if pr_or_branch is not None:
        args.insert(2, str(pr_or_branch))
    try:
        stdout = _run_gh(args)
    except RuntimeError as exc:
        if "no pull requests found" in str(exc):
            return None
        raise
    return json.loads(stdout)


def _repo_slug() -> str:
    """Return 'owner/repo' from `gh repo view --json owner,name`."""
    out = _run_gh(["repo", "view", "--json", "owner,name"])
    data = json.loads(out)
    return f"{data['owner']['login']}/{data['name']}"


def pr_checks(pr: int) -> list[dict[str, Any]]:
    out = _run_gh(["pr", "checks", str(pr), "--json", "name,status,conclusion,link"])
    return json.loads(out)


def pr_comments(pr: int) -> list[dict[str, Any]]:
    """Aggregate inline review comments, top-level issue comments, and review
    summaries into a single list of normalised {type, body, author, ...} dicts.
    """
    slug = _repo_slug()
    inline_raw = json.loads(_run_gh(["api", f"repos/{slug}/pulls/{pr}/comments"]))
    issue_raw = json.loads(_run_gh(["api", f"repos/{slug}/issues/{pr}/comments"]))
    reviews_raw = json.loads(_run_gh(["api", f"repos/{slug}/pulls/{pr}/reviews"]))

    out: list[dict[str, Any]] = []
    for c in inline_raw:
        out.append(
            {
                "type": "inline",
                "id": c["id"],
                "body": c["body"],
                "author": c.get("user", {}).get("login", ""),
                "path": c.get("path"),
                "line": c.get("line"),
                "in_reply_to": c.get("in_reply_to_id"),
                "review_id": c.get("pull_request_review_id"),
                "created_at": c.get("created_at"),
            }
        )
    for c in issue_raw:
        out.append(
            {
                "type": "top-level",
                "id": c["id"],
                "body": c["body"],
                "author": c.get("user", {}).get("login", ""),
                "created_at": c.get("created_at"),
            }
        )
    for r in reviews_raw:
        if not r.get("body"):
            continue  # skip empty review summaries
        out.append(
            {
                "type": "review",
                "id": r["id"],
                "body": r["body"],
                "author": r.get("user", {}).get("login", ""),
                "state": r.get("state"),
                "created_at": r.get("submitted_at"),
            }
        )
    return out
