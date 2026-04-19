"""Tests for unknown-command routing and CLI entry-point behaviour.

The first four tests use subprocess so that sys.argv manipulation inside
_main_entrypoint is exercised rather than bypassed by CliRunner; the
remaining tests call _main_entrypoint directly in-process to give the
coverage tracker a chance to observe the branch execution (subprocess
children do not propagate the parent's pytest-cov instrumentation).
"""

import subprocess
import sys

import pytest

from agent_experience.cli import _KNOWN_COMMANDS, _main_entrypoint


def test_unknown_command_emits_agex_page_and_exits_2(tmp_path):
    """An unknown subcommand prints agex explain agex to stdout and exits 2."""
    result = subprocess.run(
        [sys.executable, "-m", "agent_experience", "frobnicate"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode == 2
    assert "agex" in result.stdout
    assert "overview" in result.stdout
    assert "unknown command" in result.stderr.lower()


def test_known_command_still_works(tmp_path):
    """A known command (explain agex) still routes correctly and exits 0."""
    result = subprocess.run(
        [sys.executable, "-m", "agent_experience", "explain", "agex"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode == 0
    assert "agex" in result.stdout


def test_version_flag_still_works(tmp_path):
    """The --version flag bypasses the unknown-command handler and exits 0."""
    result = subprocess.run(
        [sys.executable, "-m", "agent_experience", "--version"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode == 0
    # Version string is a non-empty line on stdout
    assert result.stdout.strip() != ""


def test_zero_args_shows_help(tmp_path):
    """Invoking agex with no arguments triggers the Typer no_args_is_help path.

    Typer (via Click) exits with code 2 on no-args-help — the standard Unix
    convention for "usage error: missing required argument". We assert the
    exact code so a future regression that silently flips this to 0 is caught.
    """
    result = subprocess.run(
        [sys.executable, "-m", "agent_experience"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    combined = result.stdout + result.stderr
    assert result.returncode == 2
    assert "Usage:" in combined


# ---------------------------------------------------------------------------
# In-process tests for _main_entrypoint — the subprocess tests above exercise
# the real argv path end-to-end but do not propagate pytest-cov instrumentation
# into the child interpreter. Calling the function directly here lets coverage
# observe every branch of the router.
# ---------------------------------------------------------------------------


def test_main_entrypoint_unknown_command_exits_2(monkeypatch, capsys):
    """Direct invocation: unknown argv[0] triggers the sys.exit(2) branch."""
    monkeypatch.setattr(sys, "argv", ["agex", "frobnicate"])
    with pytest.raises(SystemExit) as excinfo:
        _main_entrypoint()
    assert excinfo.value.code == 2
    captured = capsys.readouterr()
    assert "unknown command 'frobnicate'" in captured.err
    assert "overview" in captured.out  # body of agex explain agex


def test_main_entrypoint_known_command_falls_through(monkeypatch):
    """Direct invocation: known argv[0] falls through to app() unchanged."""
    called = {"app": 0}

    def fake_app() -> None:
        called["app"] += 1

    monkeypatch.setattr(sys, "argv", ["agex", "explain", "agex"])
    monkeypatch.setattr("agent_experience.cli.app", fake_app)
    _main_entrypoint()
    assert called["app"] == 1


def test_main_entrypoint_flag_falls_through(monkeypatch):
    """Flag-led argv (e.g. --version) must bypass the unknown-command check."""
    called = {"app": 0}

    def fake_app() -> None:
        called["app"] += 1

    monkeypatch.setattr(sys, "argv", ["agex", "--version"])
    monkeypatch.setattr("agent_experience.cli.app", fake_app)
    _main_entrypoint()
    assert called["app"] == 1


def test_main_entrypoint_zero_args_falls_through(monkeypatch):
    """Empty argv falls through to app() (which then handles no_args_is_help)."""
    called = {"app": 0}

    def fake_app() -> None:
        called["app"] += 1

    monkeypatch.setattr(sys, "argv", ["agex"])
    monkeypatch.setattr("agent_experience.cli.app", fake_app)
    _main_entrypoint()
    assert called["app"] == 1


def test_known_commands_set_matches_registered_app_commands():
    """Guard: _KNOWN_COMMANDS must stay in sync with Typer's registered
    top-level commands (per the maintenance comment in cli.py)."""
    from agent_experience.cli import app, hook_app  # noqa: F401

    registered = {cmd.name for cmd in app.registered_commands}
    registered |= {grp.name for grp in app.registered_groups}
    assert _KNOWN_COMMANDS == registered


def test_dunder_main_module_imports_cleanly():
    """Exercise agent_experience/__main__.py so its top-level imports and
    `if __name__ == '__main__'` guard are observed by the coverage tracker."""
    import importlib

    module = importlib.import_module("agent_experience.__main__")
    # The module must re-export the real entry point.
    assert module._main_entrypoint is _main_entrypoint
