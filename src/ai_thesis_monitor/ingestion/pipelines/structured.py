"""Structured source ingestion pipeline."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_thesis_monitor.app.settings import Settings
from ai_thesis_monitor.db.models.analytics import NormalizedMetric
from ai_thesis_monitor.db.models.core import MetricDefinition, RawObservation, Source
from ai_thesis_monitor.ingestion.adapters.fred import FredCsvAdapter
from ai_thesis_monitor.ingestion.pipelines.features import run_feature_pipeline
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

        raw_observation = db_session.scalar(
            select(RawObservation).where(
                RawObservation.source_id == source.id,
                RawObservation.content_hash == content_hash,
            )
        )
        if raw_observation is None:
            raw_observation = RawObservation(
                source_id=source.id,
                payload=payload,
                content_hash=content_hash,
            )
            db_session.add(raw_observation)
            db_session.flush()
            raw_count += 1

        parsed_rows = parse_fred_rows(rows)
        if not parsed_rows:
            continue

        for parsed_row in parsed_rows:
            normalized_metric = db_session.scalar(
                select(NormalizedMetric).where(
                    NormalizedMetric.metric_definition_id == definition.id,
                    NormalizedMetric.source_id == source.id,
                    NormalizedMetric.observed_date == parsed_row["observed_date"],
                    NormalizedMetric.geo.is_(None),
                    NormalizedMetric.segment.is_(None),
                )
            )
            if normalized_metric is None:
                normalized_metric = NormalizedMetric(
                    metric_definition_id=definition.id,
                    source_id=source.id,
                    raw_observation_id=raw_observation.id,
                    observed_date=parsed_row["observed_date"],
                    value=parsed_row["value"],
                )
                db_session.add(normalized_metric)
            else:
                normalized_metric.raw_observation_id = raw_observation.id
                normalized_metric.value = parsed_row["value"]
            metric_count += 1

    run_feature_pipeline(db_session, metric_keys=metric_keys)
    db_session.commit()
    return StructuredPipelineResult(raw_observations=raw_count, normalized_metrics=metric_count)


def _payload_hash(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
