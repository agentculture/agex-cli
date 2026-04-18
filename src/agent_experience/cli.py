from typing import Optional

import typer

from agent_experience import __version__
from agent_experience.commands.explain.scripts import explain as explain_script

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
