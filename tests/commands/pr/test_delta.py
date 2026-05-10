from pathlib import Path

import yaml
from typer.testing import CliRunner

from agent_experience.cli import app

runner = CliRunner()


def _setup_skills_local(tmp_path: Path, siblings: list[Path]) -> None:
    (tmp_path / ".claude").mkdir(exist_ok=True)
    (tmp_path / ".claude" / "skills.local.yaml").write_text(
        yaml.safe_dump({"sibling_projects": [str(s) for s in siblings]})
    )


def _make_sibling(root: Path, name: str, claude_md: str | None, culture: dict | None) -> Path:
    p = root / name
    p.mkdir()
    if claude_md is not None:
        (p / "CLAUDE.md").write_text(claude_md)
    if culture is not None:
        (p / "culture.yaml").write_text(yaml.safe_dump(culture))
    return p


def test_delta_dumps_each_sibling(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    s1 = _make_sibling(tmp_path, "sibling-a", "Line 1\nLine 2\n", {"agents": [{"name": "a"}]})
    s2 = _make_sibling(tmp_path, "sibling-b", "Other content\n", None)
    _setup_skills_local(tmp_path, [s1, s2])
    result = runner.invoke(app, ["pr", "delta", "--agent", "claude-code"])
    assert result.exit_code == 0
    assert "sibling-a" in result.stdout
    assert "Line 1" in result.stdout
    assert "sibling-b" in result.stdout
    assert "Other content" in result.stdout
    assert "alignment drifted" in result.stdout


def test_delta_missing_skills_local(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["pr", "delta", "--agent", "claude-code"])
    assert result.exit_code == 0
    assert "skills.local.yaml" in result.stdout
    assert "skills.local.yaml.example" in result.stderr
