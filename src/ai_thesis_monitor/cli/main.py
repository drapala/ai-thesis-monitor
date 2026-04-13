"""Standalone CLI entrypoint."""

from __future__ import annotations

import typer
from sqlalchemy import select

from ai_thesis_monitor import __version__
from ai_thesis_monitor.app.db import build_session_factory
from ai_thesis_monitor.app.settings import Settings
from ai_thesis_monitor.db.models.core import MetricDefinition, Source
from ai_thesis_monitor.db.seeds.metric_definitions import METRIC_DEFINITION_SEED_ROWS
from ai_thesis_monitor.db.seeds.sources import SOURCE_SEED_ROWS

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


@app.command("seed-reference-data")
def seed_reference_data() -> None:
    """Upsert reference seed data for sources and metric definitions."""

    session_factory = build_session_factory(Settings.from_env())
    with session_factory() as session:
        for payload in SOURCE_SEED_ROWS:
            existing = session.scalar(select(Source).where(Source.source_key == payload["source_key"]))
            if existing is None:
                session.add(Source(**payload))
            else:
                for field, value in payload.items():
                    setattr(existing, field, value)

        for payload in METRIC_DEFINITION_SEED_ROWS:
            existing = session.scalar(
                select(MetricDefinition).where(MetricDefinition.metric_key == payload["metric_key"])
            )
            if existing is None:
                session.add(MetricDefinition(**payload))
            else:
                for field, value in payload.items():
                    setattr(existing, field, value)

        session.commit()

    typer.echo(
        f"Seeded reference data: {len(SOURCE_SEED_ROWS)} sources, "
        f"{len(METRIC_DEFINITION_SEED_ROWS)} metric definitions."
    )


@app.command("run-daily")
def run_daily() -> None:
    """Run the daily pipeline (placeholder)."""

    typer.echo("daily pipeline completed")


@app.command("run-weekly")
def run_weekly() -> None:
    """Run the weekly pipeline (placeholder)."""

    typer.echo("weekly pipeline completed")


@app.command("replay-week")
def replay_week_command(start_date: str, end_date: str) -> None:
    """Replay the weekly pipeline window (placeholder)."""

    typer.echo(f"replayed {start_date} to {end_date}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
