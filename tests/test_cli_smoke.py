from typer.testing import CliRunner
from agent_experience import __version__
from agent_experience.cli import app


def test_version_flag():
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout
