from typer.testing import CliRunner

from agent_experience.cli import app
from agent_experience.commands.pr.scripts import lint as lint_script

runner = CliRunner()


def _stub_git_changes(monkeypatch, files: list[tuple[str, str]]):
    """Stub `_collect_diff` to return the provided (path, content) tuples."""
    monkeypatch.setattr(lint_script, "_collect_diff", lambda: files)


def test_pr_lint_clean_emits_clean_message_and_open_hint(monkeypatch):
    _stub_git_changes(monkeypatch, [("src/foo.py", "print('hi')\n")])
    result = runner.invoke(app, ["pr", "lint", "--agent", "claude-code"])
    assert result.exit_code == 0
    assert "no violations" in result.stdout.lower()
    assert "agex pr open" in result.stdout


def test_pr_lint_reports_violations(monkeypatch):
    _stub_git_changes(
        monkeypatch,
        [("docs/x.md", "see /home/spark/.claude/foo for details\n")],
    )
    result = runner.invoke(app, ["pr", "lint", "--agent", "claude-code"])
    assert result.exit_code == 0
    assert "absolute-home-path" in result.stdout
    assert "Fix the" in result.stdout and "violation" in result.stdout


def test_pr_lint_exit_on_violation_returns_nonzero(monkeypatch):
    _stub_git_changes(monkeypatch, [("docs/x.md", "/home/spark/x\n")])
    result = runner.invoke(app, ["pr", "lint", "--agent", "claude-code", "--exit-on-violation"])
    assert result.exit_code == 1


def test_pr_lint_alignment_trigger_message(monkeypatch):
    _stub_git_changes(monkeypatch, [("CLAUDE.md", "fine content\n")])
    result = runner.invoke(app, ["pr", "lint", "--agent", "claude-code"])
    assert result.exit_code == 0
    assert "alignment" in result.stdout.lower()
    assert "agex pr delta" in result.stdout
