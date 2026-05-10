import json

from typer.testing import CliRunner

from agent_experience.cli import app
from agent_experience.commands.pr.scripts import _journal
from agent_experience.core import github

runner = CliRunner()


def _setup_post(monkeypatch, *, post_returns=None, post_side_effect=None):
    posted: list[tuple[int, str, int | None]] = []
    resolved: list[str] = []

    def fake_post(pr, body, in_reply_to):
        posted.append((pr, body, in_reply_to))
        if post_side_effect is not None:
            post_side_effect(len(posted))
        return post_returns if post_returns is not None else 1000 + len(posted)

    monkeypatch.setattr(github, "pr_post_comment", fake_post)
    monkeypatch.setattr(github, "pr_resolve_thread", lambda tid: resolved.append(tid))
    monkeypatch.setattr(github, "resolve_nick", lambda d: "agex-cli")
    return posted, resolved


def test_pr_reply_posts_and_resolves(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    posted, resolved = _setup_post(monkeypatch)

    jsonl = "\n".join(
        [
            json.dumps({"in_reply_to": 100, "thread_id": "T1", "body": "thanks"}),
            json.dumps({"thread_id": "T2", "body": "fixed"}),
        ]
    )
    result = runner.invoke(app, ["pr", "reply", "42", "--agent", "claude-code"], input=jsonl)
    assert result.exit_code == 0
    assert len(posted) == 2
    assert resolved == ["T1", "T2"]
    # Auto-signed
    assert all("- agex-cli (Claude)" in body for _, body, _ in posted)
    # Journal
    types = [e["type"] for e in _journal.load()]
    assert types.count("pr_reply") == 2
    assert types.count("pr_batch_replied") == 1


def test_pr_reply_does_not_double_sign(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    posted, _ = _setup_post(monkeypatch)
    body = "already signed\n\n- agex-cli (Claude)\n"
    jsonl = json.dumps({"in_reply_to": 1, "body": body})
    runner.invoke(app, ["pr", "reply", "42", "--agent", "claude-code"], input=jsonl)
    assert posted[0][1].count("- agex-cli (Claude)") == 1


def test_pr_reply_partial_failure_renders_resubmit_table(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    def boom_on_second(call_n):
        if call_n == 2:
            raise RuntimeError("gh failed: rate limited")

    posted, _ = _setup_post(monkeypatch, post_side_effect=boom_on_second)

    jsonl = "\n".join(
        [
            json.dumps({"in_reply_to": 100, "body": "first"}),
            json.dumps({"in_reply_to": 200, "body": "second"}),
            json.dumps({"in_reply_to": 300, "body": "third"}),  # not attempted
        ]
    )
    result = runner.invoke(app, ["pr", "reply", "42", "--agent", "claude-code"], input=jsonl)
    assert result.exit_code == 1
    assert "Failures" in result.stdout
    assert "rate limited" in result.stdout
    # First succeeded; second was attempted but raised — both got into posted[].
    assert len(posted) == 2
    # Stderr should mention resubmit
    assert "resubmit" in result.stderr.lower()


def test_pr_reply_jsonl_parse_error(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    _setup_post(monkeypatch)
    jsonl = json.dumps({"body": "ok"}) + "\n{not json\n" + json.dumps({"body": "third"})
    result = runner.invoke(app, ["pr", "reply", "42", "--agent", "claude-code"], input=jsonl)
    assert result.exit_code == 1
    assert "line 2" in result.stderr.lower() or "line 2" in result.stdout.lower()


def test_pr_reply_missing_body_field(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    posted, _ = _setup_post(monkeypatch)
    jsonl = json.dumps({"in_reply_to": 1})  # no 'body' field
    result = runner.invoke(app, ["pr", "reply", "42", "--agent", "claude-code"], input=jsonl)
    assert result.exit_code == 1
    assert "missing or invalid 'body'" in result.stdout
    assert len(posted) == 0  # no post attempted


def test_pr_reply_non_dict_jsonl_line(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    posted, _ = _setup_post(monkeypatch)
    jsonl = "[1, 2, 3]"  # valid JSON, not a dict
    result = runner.invoke(app, ["pr", "reply", "42", "--agent", "claude-code"], input=jsonl)
    assert result.exit_code == 1
    assert "missing or invalid 'body'" in result.stdout
    assert len(posted) == 0
