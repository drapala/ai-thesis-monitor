from __future__ import annotations

from sqlalchemy import select
from typer.testing import CliRunner

from ai_thesis_monitor.cli.main import app
from ai_thesis_monitor.db.models.core import MetricDefinition, Source


def test_seed_reference_data_populates_required_sources_and_metrics(
    cli_runner: CliRunner, db_session
) -> None:
    result = cli_runner.invoke(app, ["seed-reference-data"])
    assert result.exit_code == 0

    source_keys = set(db_session.scalars(select(Source.source_key)))
    assert {"fred", "rss_macro", "rss_corporate_ir"}.issubset(source_keys)

    metric_keys = set(db_session.scalars(select(MetricDefinition.metric_key)))
    assert {
        "ai_adoption_work_total",
        "labor_productivity_yoy",
        "software_postings_yoy",
        "discretionary_spending_high_income",
        "saas_renewal_discount_mentions",
        "prime_mortgage_delinquency_tech_metros",
    }.issubset(metric_keys)
