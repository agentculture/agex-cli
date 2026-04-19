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
    # Row count: exactly two `| post-tool-use |` rows, one per write
    assert result.stdout.count("| post-tool-use |") == 2


def test_hook_write_drops_empty_key_pairs(tmp_path, monkeypatch):
    import json as json_mod

    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ["hook", "write", "post-tool-use", "=orphan", "tool=Read"])
    assert result.exit_code == 0
    line = (
        (tmp_path / ".agex" / "data" / "post-tool-use.json")
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )
    payload = json_mod.loads(line)
    assert "" not in payload  # empty key dropped
    assert payload["tool"] == "Read"
    assert payload["event"] == "post-tool-use"


def test_hook_read_empty_shows_no_events(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ["hook", "read", "--agent", "claude-code"])
    assert result.exit_code == 0
    assert "_no events_" in result.stdout


def test_hook_write_rejects_path_traversal(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    for bad in ("../../etc/passwd", "/etc/passwd", "..", "a/b", "POST-TOOL-USE", "_underscore"):
        result = runner.invoke(app, ["hook", "write", bad, "k=v"])
        assert result.exit_code == 2, f"expected exit 2 for event={bad!r}"
        assert "invalid stream name" in result.stderr.lower()
        # The bad name must never land on disk.
        assert not any((tmp_path / ".agex" / "data").rglob(f"*{bad.split('/')[-1]}*"))
