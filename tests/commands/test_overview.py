import shutil
from pathlib import Path

from typer.testing import CliRunner

from agent_experience.cli import app

FIXTURES = Path(__file__).parent.parent / "fixtures" / "claude-code"


def _copy_fixture(name: str, tmp_path: Path) -> Path:
    dest = tmp_path / "project"
    shutil.copytree(FIXTURES / name, dest)
    return dest


def test_overview_typical_project(tmp_path, monkeypatch):
    project = _copy_fixture("typical", tmp_path)
    monkeypatch.chdir(project)
    runner = CliRunner()
    result = runner.invoke(app, ["overview", "--agent", "claude-code"])
    assert result.exit_code == 0
    assert "# Overview — claude-code" in result.stdout
    assert "example" in result.stdout
    assert "CLAUDE.md" in result.stdout
    assert "## Skills (1)" in result.stdout


def test_overview_empty_project(tmp_path, monkeypatch):
    project = _copy_fixture("empty", tmp_path)
    monkeypatch.chdir(project)
    runner = CliRunner()
    result = runner.invoke(app, ["overview", "--agent", "claude-code"])
    assert result.exit_code == 0
    assert result.stdout.count("_none_") == 3
    assert "no CLAUDE.md" in result.stdout
    assert "## Skills (0)" in result.stdout
    assert "## Hooks (0)" in result.stdout
    assert "## MCP servers (0)" in result.stdout


def test_overview_missing_agent_flag_errors(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ["overview"])
    assert result.exit_code != 0
    assert "agent" in (result.stderr + result.stdout).lower()


def test_overview_invalid_agent_errors(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ["overview", "--agent", "gemini"])
    assert result.exit_code == 2
    assert "gemini" in result.stderr
