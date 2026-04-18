import json

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
    assert "hooks.json" in result.stderr
    assert result.stdout == ""
    # File must be untouched.
    assert corrupt.read_text(encoding="utf-8") == "not json"


def test_gamify_install_refuses_hooks_file_with_wrong_shape(tmp_path, monkeypatch):
    # Valid JSON but shape is `list` at the top level — should refuse, not crash.
    monkeypatch.chdir(tmp_path)
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    wrong_shape = claude_dir / "hooks.json"
    original = json.dumps([{"id": "user:oops", "hook": {}}])
    wrong_shape.write_text(original, encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(app, ["gamify", "--agent", "claude-code"])
    assert result.exit_code == 2
    assert "hooks.json" in result.stderr
    assert wrong_shape.read_text(encoding="utf-8") == original


def test_gamify_uninstall_with_missing_hooks_file_clears_config(tmp_path, monkeypatch):
    # User already deleted .claude/hooks.json but config still records the
    # install. Uninstall must clear the config record WITHOUT recreating the file.
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(app, ["gamify", "--agent", "claude-code"])
    (tmp_path / ".claude" / "hooks.json").unlink()
    result = runner.invoke(app, ["gamify", "--uninstall", "--agent", "claude-code"])
    assert result.exit_code == 0
    assert not (tmp_path / ".claude" / "hooks.json").exists()
    cfg = load_config()
    assert "gamify" not in cfg.installed


def test_gamify_install_does_not_reformat_when_nothing_new(tmp_path, monkeypatch):
    # Seed hooks.json with all agex fragments already present but a non-standard
    # indentation (4 spaces instead of our 2). Re-running install should be a
    # true no-op on the file — the user's formatting choice is respected.
    monkeypatch.chdir(tmp_path)
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    seeded = {
        "PostToolUse": [
            {"id": "agex:post-tool-use", "hook": {"type": "command", "command": "agex hook write post-tool-use tool=\"$CLAUDE_TOOL_NAME\""}},
        ],
        "UserPromptSubmit": [
            {"id": "agex:user-prompt", "hook": {"type": "command", "command": "agex hook write user-prompt"}},
        ],
        "Stop": [
            {"id": "agex:stop", "hook": {"type": "command", "command": "agex hook write stop"}},
        ],
    }
    original = json.dumps(seeded, indent=4) + "\n"
    (claude_dir / "hooks.json").write_text(original, encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(app, ["gamify", "--agent", "claude-code"])
    assert result.exit_code == 0
    assert (claude_dir / "hooks.json").read_text(encoding="utf-8") == original


def test_gamify_codex_emits_unsupported_notice(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ["gamify", "--agent", "codex"])
    assert result.exit_code == 0
    assert "not supported on codex" in result.stdout.lower()
    assert "github.com" in result.stdout
    assert not (tmp_path / ".claude").exists()
