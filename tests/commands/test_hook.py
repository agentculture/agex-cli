from typer.testing import CliRunner

from agent_experience.cli import app


def test_hook_write_is_silent_and_creates_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ["hook", "write", "post-tool-use", "tool=Read"])
    assert result.exit_code == 0
    assert result.stdout == ""
    assert (tmp_path / ".agex" / "data" / "post-tool-use.json").exists()


def test_hook_read_renders_table_with_source(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(app, ["hook", "write", "post-tool-use", "tool=Read"])
    runner.invoke(app, ["hook", "write", "post-tool-use", "tool=Write"])
    result = runner.invoke(app, ["hook", "read", "--agent", "claude-code"])
    assert result.exit_code == 0
    assert "post-tool-use" in result.stdout
    assert "Source:" in result.stdout
    assert "Read" in result.stdout or "tool=Read" in result.stdout


def test_hook_read_empty_shows_no_events(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ["hook", "read", "--agent", "claude-code"])
    assert result.exit_code == 0
    assert "_no events_" in result.stdout
