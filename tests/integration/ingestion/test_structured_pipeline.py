from __future__ import annotations

from decimal import Decimal

import httpx
import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ai_thesis_monitor.ingestion.pipelines.structured import run_structured_pipeline
from ai_thesis_monitor.db.models.analytics import NormalizedMetric
from ai_thesis_monitor.db.models.core import MetricDefinition, RawObservation, Source


@pytest.fixture(autouse=True)
def clean_tables(db_session: Session) -> None:
    db_session.execute(delete(NormalizedMetric))
    db_session.execute(delete(RawObservation))
    db_session.execute(delete(MetricDefinition))
    db_session.execute(delete(Source))
    db_session.commit()
    yield
    db_session.execute(delete(NormalizedMetric))
    db_session.execute(delete(RawObservation))
    db_session.execute(delete(MetricDefinition))
    db_session.execute(delete(Source))
    db_session.commit()


def test_run_structured_pipeline_persists_latest_fred_metric(
    db_session: Session, fred_client: httpx.Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = Source(
        source_key="fred",
        source_name="Federal Reserve Economic Data",
        source_type="structured_csv",
        base_url="https://fred.stlouisfed.org",
        config={"path": "/graph/fredgraph.csv"},
        reliability_score=0.95,
        active=True,
    )
    definition = MetricDefinition(
        metric_key="unemployment_rate_professional_services",
        module_key="labor",
        name="Unemployment professional services",
        description="Unemployment rate in professional services",
        frequency="monthly",
        unit="percent",
        lag_category="confirmatory",
        weight=1.1,
        expected_direction_citadel="down",
        expected_direction_citrini="up",
        primary_feature_key="level",
        signal_transform="higher_is_citrini",
        min_history_points=6,
        is_leading=False,
        config={"source_key": "fred", "series_id": "UNRATE"},
        is_active=True,
    )
    db_session.add(source)
    db_session.add(definition)
    db_session.commit()

    monkeypatch.setenv("FRED_BASE_URL", "https://fred.example.test")

    result = run_structured_pipeline(
        db_session,
        client=fred_client,
        metric_keys=["unemployment_rate_professional_services"],
    )

    assert result.raw_observations == 1

    normalized = db_session.scalar(
        select(NormalizedMetric).where(
            NormalizedMetric.metric_definition_id == definition.id,
            NormalizedMetric.source_id == source.id,
        )
    )
    assert normalized is not None
    assert normalized.value == Decimal("4.1")
