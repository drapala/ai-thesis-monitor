"""Structured source ingestion pipeline."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_thesis_monitor.app.settings import Settings
from ai_thesis_monitor.db.models.analytics import NormalizedMetric
from ai_thesis_monitor.db.models.core import MetricDefinition, RawObservation, Source
from ai_thesis_monitor.ingestion.adapters.fred import FredCsvAdapter
from ai_thesis_monitor.ingestion.parsers.structured import parse_fred_rows


@dataclass(frozen=True)
class StructuredPipelineResult:
    raw_observations: int
    normalized_metrics: int


def run_structured_pipeline(
    db_session: Session, *, client: httpx.Client, metric_keys: list[str]
) -> StructuredPipelineResult:
    settings = Settings.from_env()
    source = db_session.scalar(select(Source).where(Source.source_key == "fred"))
    if source is None:
        raise ValueError("Source 'fred' is required")

    definitions = db_session.scalars(
        select(MetricDefinition).where(MetricDefinition.metric_key.in_(metric_keys))
    ).all()
    adapter = FredCsvAdapter(base_url=settings.fred_base_url, client=client)

    raw_count = 0
    metric_count = 0

    for definition in definitions:
        series_id = str(definition.config["series_id"])
        rows = adapter.fetch_series(series_id=series_id)

        payload = {"series_id": series_id, "rows": rows}
        content_hash = _payload_hash(payload)

        raw_observation = RawObservation(
            source_id=source.id,
            payload=payload,
            content_hash=content_hash,
        )
        db_session.add(raw_observation)
        db_session.flush()
        raw_count += 1

        latest_row = _latest_row(parse_fred_rows(rows))
        if latest_row is None:
            continue

        db_session.add(
            NormalizedMetric(
                metric_definition_id=definition.id,
                source_id=source.id,
                raw_observation_id=raw_observation.id,
                observed_date=latest_row["observed_date"],
                value=latest_row["value"],
            )
        )
        metric_count += 1

    db_session.commit()
    return StructuredPipelineResult(raw_observations=raw_count, normalized_metrics=metric_count)


def _latest_row(rows: list[dict[str, date | Decimal]]) -> dict[str, date | Decimal] | None:
    if not rows:
        return None
    return max(rows, key=lambda row: row["observed_date"])


def _payload_hash(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
