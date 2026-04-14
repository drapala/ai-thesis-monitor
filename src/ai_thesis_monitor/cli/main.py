"""Standalone CLI entrypoint."""

from __future__ import annotations

from datetime import date

import httpx
import typer
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_thesis_monitor import __version__
from ai_thesis_monitor.app.db import build_session_factory
from ai_thesis_monitor.app.settings import Settings
from ai_thesis_monitor.db.models.core import MetricDefinition, Source
from ai_thesis_monitor.db.seeds.metric_definitions import METRIC_DEFINITION_SEED_ROWS
from ai_thesis_monitor.db.seeds.sources import SOURCE_SEED_ROWS
from ai_thesis_monitor.ingestion.pipelines.features import run_feature_pipeline
from ai_thesis_monitor.ingestion.pipelines.structured import StructuredPipelineResult, run_structured_pipeline
from ai_thesis_monitor.ingestion.pipelines.text import TextPipelineResult, run_text_pipeline
from ai_thesis_monitor.ingestion.pipelines.weekly import run_weekly_pipeline
from ai_thesis_monitor.ops.replay.service import replay_week as replay_week_service

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
    """Run the daily structured/text ingestion and feature refresh pipeline."""

    session_factory = build_session_factory(Settings.from_env())
    with session_factory() as session, httpx.Client(follow_redirects=True) as client:
        metric_keys = _active_structured_metric_keys(session)
        source_keys = _active_text_source_keys(session)
        structured_result = (
            run_structured_pipeline(session, client=client, metric_keys=metric_keys)
            if metric_keys
            else StructuredPipelineResult(raw_observations=0, normalized_metrics=0)
        )
        text_result = (
            run_text_pipeline(session, client=client, source_keys=source_keys)
            if source_keys
            else TextPipelineResult(raw_observations=0, claims_created=0)
        )
        feature_result = run_feature_pipeline(session)
        session.commit()

    typer.echo(
        "daily pipeline completed: "
        f"structured_raw={structured_result.raw_observations} "
        f"normalized_metrics={structured_result.normalized_metrics} "
        f"text_raw={text_result.raw_observations} "
        f"claims={text_result.claims_created} "
        f"metric_features={feature_result.metric_features_written}"
    )


@app.command("run-weekly")
def run_weekly(score_date: str | None = typer.Argument(None)) -> None:
    """Run the weekly scoring pipeline for a specific date or today."""

    resolved_score_date = date.fromisoformat(score_date) if score_date is not None else date.today()
    session_factory = build_session_factory(Settings.from_env())
    with session_factory() as session:
        result = run_weekly_pipeline(session=session, score_date=resolved_score_date)
        session.commit()

    typer.echo(
        "weekly pipeline completed: "
        f"score_date={resolved_score_date.isoformat()} "
        f"module_scores={result.module_scores_written} "
        f"tripwires={result.tripwires_written} "
        f"alerts={result.alerts_written} "
        f"narratives={result.narratives_written}"
    )


@app.command("replay-week")
def replay_week_command(start_date: str, end_date: str) -> None:
    """Replay the weekly pipeline window (placeholder)."""

    session_factory = build_session_factory(Settings.from_env())
    with session_factory() as session:
        try:
            replay_week_service(session, start_date=start_date, end_date=end_date)
        except ValueError as exc:
            raise typer.BadParameter(str(exc))
        else:
            session.commit()

    typer.echo(f"replayed {start_date} to {end_date}")


def _active_structured_metric_keys(session: Session) -> list[str]:
    metric_definitions = session.scalars(
        select(MetricDefinition).where(MetricDefinition.is_active.is_(True))
    ).all()
    return [
        definition.metric_key
        for definition in metric_definitions
        if definition.config.get("source_key") == "fred"
    ]


def _active_text_source_keys(session: Session) -> list[str]:
    sources = session.scalars(
        select(Source).where(Source.active.is_(True), Source.source_type == "rss")
    ).all()
    return [source.source_key for source in sources]


def main() -> None:
    app()


if __name__ == "__main__":
    main()
