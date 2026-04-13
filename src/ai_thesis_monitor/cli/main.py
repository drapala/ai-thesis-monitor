"""Standalone CLI entrypoint."""

from __future__ import annotations

import typer

from ai_thesis_monitor import __version__

app = typer.Typer(
    name="ai-thesis-monitor",
    help="AI Thesis Monitor CLI",
    invoke_without_command=True,
)


@app.callback(invoke_without_command=True)
def _root(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command()
def version() -> None:
    """Print the currently-deployed release version."""

    typer.echo(__version__)
