"""`agex pr reply` — batch JSONL replies + thread resolution."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from agent_experience.commands.pr.assets.rules.next_step_rules import reply_next_step
from agent_experience.commands.pr.scripts import _journal
from agent_experience.commands.pr.scripts._footer import render_footer
from agent_experience.core import github
from agent_experience.core.backend import resolve_backend
from agent_experience.core.render import render_string

_TEMPLATES_PKG = "agent_experience.commands.pr.assets.templates"


@dataclass
class _Failure:
    line: int
    reason: str
    entry: str


def _signed(body: str, nick: str) -> str:
    sig = f"- {nick} (Claude)"
    if sig in body:
        return body
    sep = "" if body.endswith("\n") else "\n"
    return f"{body}{sep}\n{sig}\n"


def run(
    agent: str | None,
    project_dir: Path,
    pr: int,
) -> tuple[str, int, str]:
    backend = resolve_backend(agent, project_dir)
    nick = github.resolve_nick(project_dir)
    raw = sys.stdin.read()

    posted = 0
    resolved = 0
    failures: list[_Failure] = []
    parse_error_line: int | None = None

    for lineno, raw_line in enumerate(raw.splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            entry = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            parse_error_line = lineno
            failures.append(
                _Failure(line=lineno, reason=f"JSONL parse error: {exc}", entry=raw_line)
            )
            break  # stop processing — caller fixes line and resubmits the slice
        body = _signed(entry["body"], nick)
        try:
            github.pr_post_comment(pr=pr, body=body, in_reply_to=entry.get("in_reply_to"))
            posted += 1
            _journal.append(
                {
                    "type": "pr_reply",
                    "pr": pr,
                    "thread_id": entry.get("thread_id"),
                    "in_reply_to": entry.get("in_reply_to"),
                }
            )
            if entry.get("thread_id"):
                github.pr_resolve_thread(entry["thread_id"])
                resolved += 1
        except RuntimeError as exc:
            failures.append(_Failure(line=lineno, reason=str(exc), entry=raw_line))
            break  # stop on first network failure to keep recovery simple

    _journal.append({"type": "pr_batch_replied", "pr": pr, "count": posted, "resolved": resolved})

    footer_key, footer_ctx = reply_next_step(pr=pr, failure_count=len(failures))
    footer = render_footer(footer_key, backend, footer_ctx)

    template = files(_TEMPLATES_PKG).joinpath("pr_reply_result.md.j2").read_text(encoding="utf-8")
    stdout = render_string(
        template,
        {
            "pr": pr,
            "count": posted,
            "resolved": resolved,
            "failures": [f.__dict__ for f in failures],
            "footer": footer,
        },
    )
    if failures:
        if parse_error_line is not None:
            stderr = (
                f"agex: fix line {parse_error_line} (see stdout) and resubmit "
                f"lines {parse_error_line}..end to 'agex pr reply {pr}'\n"
            )
        else:
            first_failed = failures[0].line
            stderr = (
                f"agex: resubmit lines {first_failed}..end from the table above "
                f"to 'agex pr reply {pr}'\n"
            )
        return stdout, 1, stderr
    return stdout, 0, ""
