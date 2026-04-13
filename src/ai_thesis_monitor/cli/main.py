"""Standalone CLI entrypoint."""

from __future__ import annotations

import typer

from ai_thesis_monitor import __version__

app = typer.Typer(help="AI Thesis Monitor CLI")


@app.callback(invoke_without_command=True)
def _root() -> None:
    """Entry point for the CLI group."""


@app.command()
def version() -> None:
    """Print the currently-deployed release version."""

    typer.echo(__version__)
