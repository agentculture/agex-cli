import sys
from pathlib import Path
from typing import Any, Optional

import typer

from agent_experience import __version__
from agent_experience.commands.doctor.scripts import doctor as doctor_script
from agent_experience.commands.explain.scripts import explain as explain_script
from agent_experience.commands.gamify.scripts import install as gamify_script
from agent_experience.commands.hook.scripts import read as hook_read_script
from agent_experience.commands.hook.scripts import write as hook_write_script
from agent_experience.commands.learn.scripts import learn as learn_script
from agent_experience.commands.overview.scripts import overview as overview_script
from agent_experience.commands.pr.scripts import lint as pr_lint_script
from agent_experience.commands.pr.scripts import open_ as pr_open_script
from agent_experience.commands.pr.scripts import read as pr_read_script
from agent_experience.commands.pr.scripts import reply as pr_reply_script
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


@app.command("doctor")
def doctor(
    role: Optional[str] = typer.Option(
        None, "--role", help="Render a role-specific check section (e.g., pr-review)."
    ),
) -> None:
    stdout, exit_code, stderr = doctor_script.run(role)
    if stdout:
        typer.echo(stdout, nl=False)
    if stderr:
        typer.echo(stderr, err=True)
    if exit_code != 0:
        raise typer.Exit(code=exit_code)


def _agent_option() -> Any:
    return typer.Option(..., "--agent", help="Backend: claude-code, codex, copilot, or acp.")


hook_app = typer.Typer(help="Write and read agex tracking events.", no_args_is_help=True)
app.add_typer(hook_app, name="hook")


@hook_app.command("write")
def hook_write(
    event: str = typer.Argument(..., help="Event name (e.g., post-tool-use)."),
    args: list[str] = typer.Argument(None, help="Additional key=value pairs."),
) -> None:
    args = args or []
    _, exit_code, stderr = hook_write_script.run(event, args)
    if stderr:
        typer.echo(stderr, err=True)
    if exit_code != 0:
        raise typer.Exit(code=exit_code)


@hook_app.command("read")
def hook_read(agent: str = _agent_option()) -> None:
    try:
        backend = parse_backend(agent)
    except ValueError as e:
        typer.echo(f"agex: error: {e}", err=True)
        raise typer.Exit(code=2)
    stdout, exit_code, stderr = hook_read_script.run(backend)
    if stdout:
        typer.echo(stdout, nl=False)
    if stderr:
        typer.echo(stderr, err=True)
    if exit_code != 0:
        raise typer.Exit(code=exit_code)


pr_app = typer.Typer(name="pr", help="GitHub PR lifecycle commands.", no_args_is_help=True)
app.add_typer(pr_app, name="pr")


@pr_app.command("lint")
def pr_lint(
    agent: Optional[str] = typer.Option(
        None, "--agent", help="Backend (claude-code|codex|copilot|acp); falls back to culture.yaml."
    ),
    exit_on_violation: bool = typer.Option(
        False, "--exit-on-violation", help="Exit 1 when violations are found (CI mode)."
    ),
) -> None:
    try:
        stdout, exit_code, stderr = pr_lint_script.run(
            agent=agent, project_dir=Path.cwd(), exit_on_violation=exit_on_violation
        )
    except ValueError as exc:
        typer.echo(f"agex: {exc}", err=True)
        raise typer.Exit(code=2)
    if stdout:
        typer.echo(stdout, nl=False)
    if stderr:
        typer.echo(stderr, err=True)
    if exit_code != 0:
        raise typer.Exit(code=exit_code)


@pr_app.command("open")
def pr_open(
    title: str = typer.Option(..., "--title"),
    body_file: Optional[Path] = typer.Option(None, "--body-file"),
    draft: bool = typer.Option(False, "--draft"),
    agent: Optional[str] = typer.Option(None, "--agent"),
    delayed_read: bool = typer.Option(
        False,
        "--delayed-read",
        help="After create, immediately run `pr read --wait 180`.",
    ),
) -> None:
    try:
        stdout, exit_code, stderr = pr_open_script.run(
            agent=agent,
            project_dir=Path.cwd(),
            title=title,
            body_file=body_file,
            draft=draft,
            delayed_read=delayed_read,
        )
    except ValueError as exc:
        typer.echo(f"agex: {exc}", err=True)
        raise typer.Exit(code=2)
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        typer.echo("agex: rerun 'agex pr open ...' once network is reachable", err=True)
        raise typer.Exit(code=1)
    if stdout:
        typer.echo(stdout, nl=False)
    if stderr:
        typer.echo(stderr, err=True)
    if exit_code != 0:
        raise typer.Exit(code=exit_code)


@pr_app.command("reply")
def pr_reply(
    pr: int = typer.Argument(...),
    agent: Optional[str] = typer.Option(None, "--agent"),
) -> None:
    try:
        stdout, exit_code, stderr = pr_reply_script.run(agent=agent, project_dir=Path.cwd(), pr=pr)
    except ValueError as exc:
        typer.echo(f"agex: {exc}", err=True)
        raise typer.Exit(code=2)
    if stdout:
        typer.echo(stdout, nl=False)
    if stderr:
        typer.echo(stderr, err=True, nl=False)
    if exit_code != 0:
        raise typer.Exit(code=exit_code)


@pr_app.command("read")
def pr_read(
    pr: Optional[int] = typer.Argument(None),
    wait: Optional[int] = typer.Option(
        None, "--wait", help="Poll for readiness up to SECS seconds."
    ),
    agent: Optional[str] = typer.Option(None, "--agent"),
) -> None:
    try:
        stdout, exit_code, stderr = pr_read_script.run(
            agent=agent, project_dir=Path.cwd(), pr=pr, wait=wait
        )
    except ValueError as exc:
        typer.echo(f"agex: {exc}", err=True)
        raise typer.Exit(code=2)
    if stdout:
        typer.echo(stdout, nl=False)
    if stderr:
        typer.echo(stderr, err=True)
    if exit_code != 0:
        raise typer.Exit(code=exit_code)


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


@app.command("gamify")
def gamify(
    agent: str = _agent_option(),
    uninstall: bool = typer.Option(False, "--uninstall", help="Reverse gamify."),
) -> None:
    try:
        backend = parse_backend(agent)
    except ValueError as e:
        typer.echo(f"agex: error: {e}", err=True)
        raise typer.Exit(code=2)
    if uninstall:
        stdout, exit_code, stderr = gamify_script.uninstall(backend)
    else:
        stdout, exit_code, stderr = gamify_script.install(backend)
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


# Keep in sync with the @app.command / app.add_typer registrations above.
# If a new top-level command is added, extend this set so _main_entrypoint
# stops routing it to the unknown-command fallback page.
_KNOWN_COMMANDS = {"explain", "overview", "learn", "gamify", "hook", "doctor", "pr"}


def _main_entrypoint() -> None:
    """CLI entry point that routes unknown subcommands to ``agex explain agex``.

    When the first positional argument is not a known command (and is not a
    flag), this function prints the ``agex explain agex`` page to stdout and
    the canonical error message to stderr, then exits with code 2.  All other
    invocations — known commands, ``--version``, ``--help``, zero-arg help —
    fall through to the normal Typer ``app()`` dispatch unchanged.
    """
    argv = sys.argv[1:]
    if argv and not argv[0].startswith("-") and argv[0] not in _KNOWN_COMMANDS:
        typer.echo(f"agex: error: unknown command '{argv[0]}'", err=True)
        stdout, _, _ = explain_script.run("agex")
        typer.echo(stdout, nl=False)
        sys.exit(2)
    app()
