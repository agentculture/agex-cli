from typer.testing import CliRunner

from agent_experience.cli import app
from agent_experience.commands.pr.scripts import _journal
from agent_experience.core import github

runner = CliRunner()


def _patch(monkeypatch, *, view_returns, create_returns_pr=42, captured=None):
    if captured is None:
        captured = {}
    monkeypatch.setattr(github, "pr_view", lambda branch=None: view_returns)
    monkeypatch.setattr(github, "resolve_nick", lambda d: "agex-cli")

    def fake_create(title, body, draft):
        captured["title"] = title
        captured["body"] = body
        captured["draft"] = draft
        return create_returns_pr

    monkeypatch.setattr(github, "pr_create", fake_create)
    return captured


def test_pr_open_creates_pr_and_signs_body(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    captured = _patch(monkeypatch, view_returns=None)
    body_file = tmp_path / "body.md"
    body_file.write_text("Some PR body without signature.\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "pr",
            "open",
            "--agent",
            "claude-code",
            "--title",
            "feat: x",
            "--body-file",
            str(body_file),
        ],
    )
    assert result.exit_code == 0
    assert captured["title"] == "feat: x"
    assert "- agex-cli (Claude)" in captured["body"]
    assert captured["draft"] is False
    assert "PR opened" in result.stdout
    assert "#42" in result.stdout
    assert "agex pr read 42 --wait 180" in result.stdout


def test_pr_open_does_not_double_sign(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    captured = _patch(monkeypatch, view_returns=None)
    body_file = tmp_path / "body.md"
    body_file.write_text("Body.\n\n- agex-cli (Claude)\n", encoding="utf-8")

    runner.invoke(
        app, ["pr", "open", "--agent", "claude-code", "--title", "t", "--body-file", str(body_file)]
    )
    assert captured["body"].count("- agex-cli (Claude)") == 1


def test_pr_open_idempotent_when_pr_already_exists(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    create_called = {"n": 0}
    monkeypatch.setattr(github, "pr_view", lambda branch=None: {"number": 7, "state": "OPEN"})
    monkeypatch.setattr(github, "resolve_nick", lambda d: "agex-cli")

    def fake_create(*args, **kwargs):
        create_called["n"] += 1
        return 999

    monkeypatch.setattr(github, "pr_create", fake_create)

    body_file = tmp_path / "body.md"
    body_file.write_text("body\n", encoding="utf-8")
    result = runner.invoke(
        app, ["pr", "open", "--agent", "claude-code", "--title", "t", "--body-file", str(body_file)]
    )
    assert result.exit_code == 0
    assert create_called["n"] == 0
    assert "already open" in result.stdout.lower()
    assert "agex pr read 7" in result.stdout


def test_pr_open_writes_journal_event(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    _patch(monkeypatch, view_returns=None)
    body_file = tmp_path / "body.md"
    body_file.write_text("b\n", encoding="utf-8")
    runner.invoke(
        app, ["pr", "open", "--agent", "claude-code", "--title", "t", "--body-file", str(body_file)]
    )
    events = _journal.load()
    types = [e["type"] for e in events]
    assert "pr_opened" in types
    opened = next(e for e in events if e["type"] == "pr_opened")
    assert opened["pr"] == 42
    assert opened["title"] == "t"


def test_pr_open_draft_flag(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    captured = _patch(monkeypatch, view_returns=None)
    body_file = tmp_path / "body.md"
    body_file.write_text("b\n", encoding="utf-8")
    runner.invoke(
        app,
        [
            "pr",
            "open",
            "--agent",
            "claude-code",
            "--title",
            "t",
            "--body-file",
            str(body_file),
            "--draft",
        ],
    )
    assert captured["draft"] is True
