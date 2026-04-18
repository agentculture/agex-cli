import json
from datetime import datetime, timezone
from pathlib import Path

from typer.testing import CliRunner

from agent_experience.cli import app
from agent_experience.core.config import load as load_config


def test_gamify_install_writes_hooks_and_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ["gamify", "--agent", "claude-code"])
    assert result.exit_code == 0

    hooks_file = tmp_path / ".claude" / "hooks.json"
    assert hooks_file.exists()
    data = json.loads(hooks_file.read_text())
    assert "PostToolUse" in data
    assert any(h["id"] == "agex:post-tool-use" for h in data["PostToolUse"])

    cfg = load_config()
    assert "gamify" in cfg.installed
    assert sorted(cfg.installed["gamify"]["hook_fragment_ids"]) == [
        "agex:post-tool-use",
        "agex:stop",
        "agex:user-prompt",
    ]


def test_gamify_install_idempotent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(app, ["gamify", "--agent", "claude-code"])
    first = (tmp_path / ".claude" / "hooks.json").read_text()
    result = runner.invoke(app, ["gamify", "--agent", "claude-code"])
    assert result.exit_code == 0
    second = (tmp_path / ".claude" / "hooks.json").read_text()
    assert first == second


def test_gamify_install_preserves_user_hooks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    (claude_dir / "hooks.json").write_text(json.dumps({
        "PostToolUse": [{"id": "user:custom", "hook": {"type": "command", "command": "echo hi"}}]
    }))
    runner = CliRunner()
    runner.invoke(app, ["gamify", "--agent", "claude-code"])
    data = json.loads((claude_dir / "hooks.json").read_text())
    ids = [h["id"] for h in data["PostToolUse"]]
    assert "user:custom" in ids
    assert "agex:post-tool-use" in ids


def test_gamify_uninstall_removes_only_agex_fragments(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    (claude_dir / "hooks.json").write_text(json.dumps({
        "PostToolUse": [{"id": "user:custom", "hook": {"type": "command", "command": "echo hi"}}]
    }))
    runner = CliRunner()
    runner.invoke(app, ["gamify", "--agent", "claude-code"])
    result = runner.invoke(app, ["gamify", "--uninstall", "--agent", "claude-code"])
    assert result.exit_code == 0
    data = json.loads((claude_dir / "hooks.json").read_text())
    ids = [h["id"] for h in data["PostToolUse"]]
    assert ids == ["user:custom"]

    cfg = load_config()
    assert "gamify" not in cfg.installed


def test_gamify_install_refuses_to_overwrite_corrupt_hooks_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    corrupt = claude_dir / "hooks.json"
    corrupt.write_text("not json", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(app, ["gamify", "--agent", "claude-code"])
    assert result.exit_code == 2
    assert "hooks.json" in result.output
    # File must be untouched.
    assert corrupt.read_text(encoding="utf-8") == "not json"
