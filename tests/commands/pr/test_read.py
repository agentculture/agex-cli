from typer.testing import CliRunner

from agent_experience.cli import app
from agent_experience.commands.pr.scripts import _journal
from agent_experience.core import github

runner = CliRunner()


def _setup_clean(monkeypatch, *, comments=None, checks=None):
    monkeypatch.setattr(
        github,
        "pr_view",
        lambda x: {
            "number": 42,
            "state": "OPEN",
            "title": "t",
            "url": "u",
            "headRefName": "h",
            "baseRefName": "main",
        },
    )
    monkeypatch.setattr(github, "pr_checks", lambda pr: checks or [])
    monkeypatch.setattr(github, "pr_comments", lambda pr: comments or [])
    monkeypatch.setattr(github, "sonar_quality_gate", lambda *a, **k: None)
    monkeypatch.setattr(github, "sonar_new_issues", lambda *a, **k: [])
    # Avoid network round-trip in _project_key derivation:
    monkeypatch.setattr(github, "_repo_slug", lambda: "owner/repo")


def test_pr_read_one_shot_renders_briefing(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    _setup_clean(monkeypatch)
    result = runner.invoke(app, ["pr", "read", "42", "--agent", "claude-code"])
    assert result.exit_code == 0
    assert "PR #42" in result.stdout
    assert "Wait for human merge" in result.stdout


def test_pr_read_with_failing_check(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    _setup_clean(
        monkeypatch,
        checks=[{"name": "test", "status": "completed", "conclusion": "failure"}],
    )
    result = runner.invoke(app, ["pr", "read", "42", "--agent", "claude-code"])
    assert "Fix CI" in result.stdout


def test_pr_read_with_comments_emits_table(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    _setup_clean(
        monkeypatch,
        comments=[
            {
                "type": "inline",
                "id": 1,
                "body": "nit: rename",
                "author": "qodo[bot]",
                "path": "src/foo.py",
                "line": 12,
            }
        ],
    )
    result = runner.invoke(app, ["pr", "read", "42", "--agent", "claude-code"])
    assert "src/foo.py:12" in result.stdout
    assert "qodo" in result.stdout


def test_pr_read_writes_journal_event(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    _setup_clean(monkeypatch)
    runner.invoke(app, ["pr", "read", "42", "--agent", "claude-code"])
    events = _journal.load()
    assert any(e["type"] == "pr_read" and e["pr"] == 42 for e in events)
