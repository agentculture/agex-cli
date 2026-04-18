from typer.testing import CliRunner

from agent_experience.cli import app


def test_learn_menu_lists_introspect():
    runner = CliRunner()
    result = runner.invoke(app, ["learn", "--agent", "claude-code"])
    assert result.exit_code == 0
    assert "introspect" in result.stdout


def test_learn_introspect_emits_lesson_and_template():
    runner = CliRunner()
    result = runner.invoke(app, ["learn", "introspect", "--agent", "claude-code"])
    assert result.exit_code == 0
    assert "build an `introspect` skill" in result.stdout
    # Template body embedded as code block
    assert "Audit the current project" in result.stdout


def test_learn_unknown_topic_errors_with_menu():
    runner = CliRunner()
    result = runner.invoke(app, ["learn", "xyz", "--agent", "claude-code"])
    assert result.exit_code == 2
    assert "unknown topic" in result.stderr.lower()
    assert "introspect" in result.stdout  # menu in stdout


def test_learn_rejects_path_traversal():
    runner = CliRunner()
    for bad in ("../../../etc/passwd", "/etc/passwd", "..", "a/b", "INTROSPECT"):
        result = runner.invoke(app, ["learn", bad, "--agent", "claude-code"])
        assert result.exit_code == 2, f"expected exit 2 for topic={bad!r}"
        assert "unknown topic" in result.stderr.lower()
