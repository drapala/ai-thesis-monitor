from __future__ import annotations

from datetime import date
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import delete, func, select
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


def test_run_structured_pipeline_replay_identical_payload_is_idempotent(
    db_session: Session, fred_client: httpx.Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, definition = _seed_fred_metric(db_session)
    monkeypatch.setenv("FRED_BASE_URL", "https://fred.example.test")

    run_structured_pipeline(
        db_session,
        client=fred_client,
        metric_keys=["unemployment_rate_professional_services"],
    )
    run_structured_pipeline(
        db_session,
        client=fred_client,
        metric_keys=["unemployment_rate_professional_services"],
    )

    raw_count = db_session.scalar(select(func.count()).select_from(RawObservation))
    metric_count = db_session.scalar(select(func.count()).select_from(NormalizedMetric))
    normalized = db_session.scalar(
        select(NormalizedMetric).where(
            NormalizedMetric.metric_definition_id == definition.id,
            NormalizedMetric.source_id == source.id,
        )
    )

    assert raw_count == 1
    assert metric_count == 1
    assert normalized is not None
    assert normalized.value == Decimal("4.1")


def test_run_structured_pipeline_revised_payload_updates_semantic_metric_row(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, definition = _seed_fred_metric(db_session)
    monkeypatch.setenv("FRED_BASE_URL", "https://fred.example.test")

    payloads = [
        "DATE,VALUE\n2026-01-01,.\n2026-02-01,4.1\n",
        "DATE,VALUE\n2026-01-01,.\n2026-02-01,4.2\n",
    ]
    call_count = {"value": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/graph/fredgraph.csv"
        assert request.url.params.get("id") == "UNRATE"
        body = payloads[min(call_count["value"], len(payloads) - 1)]
        call_count["value"] += 1
        return httpx.Response(200, text=body)

    client = httpx.Client(base_url="https://fred.example.test", transport=httpx.MockTransport(handler))
    try:
        run_structured_pipeline(
            db_session,
            client=client,
            metric_keys=["unemployment_rate_professional_services"],
        )
        run_structured_pipeline(
            db_session,
            client=client,
            metric_keys=["unemployment_rate_professional_services"],
        )
    finally:
        client.close()

    raw_count = db_session.scalar(select(func.count()).select_from(RawObservation))
    metric_count = db_session.scalar(select(func.count()).select_from(NormalizedMetric))
    normalized = db_session.scalar(
        select(NormalizedMetric).where(
            NormalizedMetric.metric_definition_id == definition.id,
            NormalizedMetric.source_id == source.id,
            NormalizedMetric.observed_date == date(2026, 2, 1),
        )
    )
    latest_raw = db_session.scalar(select(RawObservation).order_by(RawObservation.id.desc()))

    assert raw_count == 2
    assert metric_count == 1
    assert normalized is not None
    assert latest_raw is not None
    assert normalized.value == Decimal("4.2")
    assert normalized.raw_observation_id == latest_raw.id


def _seed_fred_metric(db_session: Session) -> tuple[Source, MetricDefinition]:
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
    return source, definition
