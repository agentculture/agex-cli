import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agent_experience import __version__
from agent_experience.cli import app
from agent_experience.core.paths import GITIGNORE_CONTENT


@pytest.fixture
def in_tmp_cwd(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Run each test in an isolated cwd so `.agex/` lookups don't leak."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _init_agex(root: Path, *, agex_version: str = __version__) -> None:
    agex = root / ".agex"
    agex.mkdir()
    (agex / "data").mkdir()
    (agex / ".gitignore").write_text(GITIGNORE_CONTENT, encoding="utf-8")
    (agex / "config.toml").write_text(f'agex_version = "{agex_version}"\n', encoding="utf-8")


def test_doctor_runs_with_no_args_and_exits_zero(in_tmp_cwd: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0, result.output
    assert "# agex doctor" in result.stdout
    assert "## Install" in result.stdout
    assert "## Project state" in result.stdout
    assert "## Internal consistency" in result.stdout
    assert "## Operator verification" in result.stdout
    assert "## Summary" in result.stdout


def test_doctor_reports_uninitialized_agex_dir_as_info(in_tmp_cwd: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "not initialized" in result.stdout
    # No hard failure markers in any check row.
    assert "✗" not in result.stdout or "✗ fail | 0" in result.stdout


def test_doctor_does_not_create_agex_dir(in_tmp_cwd: Path) -> None:
    runner = CliRunner()
    runner.invoke(app, ["doctor"])
    assert not (in_tmp_cwd / ".agex").exists(), "doctor must remain read-only"


def test_doctor_with_initialized_agex_dir_reports_ok(in_tmp_cwd: Path) -> None:
    _init_agex(in_tmp_cwd)
    runner = CliRunner()
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "✓ **`.agex/` directory**" in result.stdout
    assert "✓ **`.agex/config.toml`**" in result.stdout
    assert "✓ **`.agex/.gitignore`**" in result.stdout
    assert "✓ **`.agex/data/`**" in result.stdout


def test_doctor_detects_invalid_config_toml(in_tmp_cwd: Path) -> None:
    agex = in_tmp_cwd / ".agex"
    agex.mkdir()
    (agex / "data").mkdir()
    (agex / ".gitignore").write_text(GITIGNORE_CONTENT, encoding="utf-8")
    (agex / "config.toml").write_text("invalid = = toml", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "✗ **`.agex/config.toml`**" in result.stdout
    assert "agex: error:" in result.stderr
    assert "health check" in result.stderr


def test_doctor_detects_version_mismatch_as_warning(in_tmp_cwd: Path) -> None:
    _init_agex(in_tmp_cwd, agex_version="0.0.0-old")
    runner = CliRunner()
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "⚠️ **`.agex/config.toml`**" in result.stdout
    assert "0.0.0-old" in result.stdout


def test_doctor_detects_drifted_gitignore(in_tmp_cwd: Path) -> None:
    _init_agex(in_tmp_cwd)
    (in_tmp_cwd / ".agex" / ".gitignore").write_text("# hand-edited\n", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "⚠️ **`.agex/.gitignore`**" in result.stdout
    assert "drifted" in result.stdout


def test_doctor_detects_missing_gitignore(in_tmp_cwd: Path) -> None:
    _init_agex(in_tmp_cwd)
    (in_tmp_cwd / ".agex" / ".gitignore").unlink()
    runner = CliRunner()
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "⚠️ **`.agex/.gitignore`**" in result.stdout
    assert "missing" in result.stdout


def test_doctor_detects_unwritable_data_dir(in_tmp_cwd: Path) -> None:
    _init_agex(in_tmp_cwd)
    data = in_tmp_cwd / ".agex" / "data"
    original_mode = data.stat().st_mode
    os.chmod(data, 0o500)  # readable + executable, not writable
    try:
        runner = CliRunner()
        result = runner.invoke(app, ["doctor"])
        # Skip on platforms that ignore chmod (e.g. some Windows + WSL combos).
        if os.access(data, os.W_OK):
            pytest.skip("filesystem ignores chmod; cannot exercise unwritable case")
        assert result.exit_code == 1
        assert "✗ **`.agex/data/`**" in result.stdout
    finally:
        os.chmod(data, original_mode)


def test_doctor_internal_consistency_passes(in_tmp_cwd: Path) -> None:
    """Sanity: every shipped SKILL.md and capability YAML must parse."""
    runner = CliRunner()
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "✓ **Shipped SKILL.md frontmatter**" in result.stdout
    assert "✓ **Backend capability YAML**" in result.stdout


def test_doctor_summary_table_appears(in_tmp_cwd: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "| ✓ ok |" in result.stdout
    assert "| ⚠️ warn |" in result.stdout
    assert "| ✗ fail |" in result.stdout
    assert "| · info |" in result.stdout


def test_doctor_unknown_role_exits_2(in_tmp_cwd: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["doctor", "--role", "no-such-role"])
    assert result.exit_code == 2
    assert "unknown role" in result.stderr


def test_doctor_rejects_role_path_traversal(in_tmp_cwd: Path) -> None:
    runner = CliRunner()
    for bad in ("../../../etc/passwd", "/etc/passwd", "..", "a/b", "PrRev"):
        result = runner.invoke(app, ["doctor", "--role", bad])
        assert result.exit_code == 2, f"expected exit 2 for role={bad!r}"


def test_doctor_role_renders_extra_section(
    in_tmp_cwd: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ship a temporary role file via monkeypatch and confirm it renders."""
    from agent_experience.commands.doctor.scripts import doctor as doctor_module

    fake_section = "Custom role check: confirm credentials are present."

    class _FakeTraversable:
        def is_file(self) -> bool:
            return True

        def read_text(self, encoding: str = "utf-8") -> str:
            return fake_section

    def _fake_resolve(role: str):
        return _FakeTraversable() if role == "pr-review" else None

    monkeypatch.setattr(doctor_module, "_resolve_role", _fake_resolve)

    runner = CliRunner()
    result = runner.invoke(app, ["doctor", "--role", "pr-review"])
    assert result.exit_code == 0, result.output
    assert "## Role: `pr-review`" in result.stdout
    assert fake_section in result.stdout
