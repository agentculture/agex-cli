from typing import Any, Optional

import typer

from agent_experience import __version__
from agent_experience.commands.explain.scripts import explain as explain_script
from agent_experience.commands.learn.scripts import learn as learn_script
from agent_experience.commands.overview.scripts import overview as overview_script
from agent_experience.core.backend import parse_backend

app = typer.Typer(
    name="agex",
    help="Agent-operated developer-experience CLI.",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", callback=_version_callback, is_eager=True
    ),
) -> None:
    """Root callback — exists only to hold the --version option.

    Typer invokes the eager _version_callback before any subcommand
    dispatch; there is nothing else to do at the app level.
    """


@app.command("explain")
def explain(topic: str = typer.Argument(..., help="Topic to explain.")) -> None:
    stdout, exit_code, stderr = explain_script.run(topic)
    if stdout:
        typer.echo(stdout, nl=False)
    if stderr:
        typer.echo(stderr, err=True)
    if exit_code != 0:
        raise typer.Exit(code=exit_code)


def _agent_option() -> Any:
    return typer.Option(..., "--agent", help="Backend: claude-code, codex, copilot, or acp.")


@app.command("learn")
def learn(
    topic: Optional[str] = typer.Argument(None, help="Lesson topic (omit for menu)."),
    agent: str = _agent_option(),
) -> None:
    try:
        backend = parse_backend(agent)
    except ValueError as e:
        typer.echo(f"agex: error: {e}", err=True)
        raise typer.Exit(code=2)
    if topic is None:
        stdout, exit_code, stderr = learn_script.run_menu(backend)
    else:
        stdout, exit_code, stderr = learn_script.run_topic(topic, backend)
    if stdout:
        typer.echo(stdout, nl=False)
    if stderr:
        typer.echo(stderr, err=True)
    if exit_code != 0:
        raise typer.Exit(code=exit_code)


@app.command("overview")
def overview(agent: str = _agent_option()) -> None:
    try:
        backend = parse_backend(agent)
    except ValueError as e:
        typer.echo(f"agex: error: {e}", err=True)
        raise typer.Exit(code=2)
    stdout, exit_code, stderr = overview_script.run(backend)
    if stdout:
        typer.echo(stdout, nl=False)
    if stderr:
        typer.echo(stderr, err=True)
    if exit_code != 0:
        raise typer.Exit(code=exit_code)
