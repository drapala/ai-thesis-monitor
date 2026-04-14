"""Derived metric feature persistence pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_thesis_monitor.db.models.analytics import MetricFeature, NormalizedMetric
from ai_thesis_monitor.db.models.core import MetricDefinition
from ai_thesis_monitor.domain.metrics.features import build_feature_payload, serialize_feature_payload


@dataclass(frozen=True)
class FeaturePipelineResult:
    metric_features_written: int


def run_feature_pipeline(
    session: Session,
    *,
    metric_keys: list[str] | None = None,
    observed_date_lte: date | None = None,
) -> FeaturePipelineResult:
    query = (
        select(NormalizedMetric, MetricDefinition)
        .join(MetricDefinition, MetricDefinition.id == NormalizedMetric.metric_definition_id)
        .order_by(
            NormalizedMetric.metric_definition_id,
            NormalizedMetric.source_id,
            NormalizedMetric.geo,
            NormalizedMetric.segment,
            NormalizedMetric.observed_date,
            NormalizedMetric.id,
        )
    )
    if metric_keys is not None:
        query = query.where(MetricDefinition.metric_key.in_(metric_keys))
    if observed_date_lte is not None:
        query = query.where(NormalizedMetric.observed_date <= observed_date_lte)

    rows = session.execute(query).all()
    if not rows:
        return FeaturePipelineResult(metric_features_written=0)

    normalized_metric_ids = [metric.id for metric, _ in rows]
    existing_features = {
        feature.normalized_metric_id: feature
        for feature in session.scalars(
            select(MetricFeature).where(MetricFeature.normalized_metric_id.in_(normalized_metric_ids))
        )
    }

    grouped_rows: dict[tuple[int, int, str | None, str | None], list[tuple[NormalizedMetric, MetricDefinition]]] = {}
    for metric, definition in rows:
        semantic_key = (metric.metric_definition_id, metric.source_id, metric.geo, metric.segment)
        grouped_rows.setdefault(semantic_key, []).append((metric, definition))

    written = 0
    for series_rows in grouped_rows.values():
        series: list[Decimal] = []
        for metric, definition in series_rows:
            series.append(metric.value)
            payload = serialize_feature_payload(
                build_feature_payload(series=series, frequency=definition.frequency)
            )
            feature = existing_features.get(metric.id)
            if feature is None:
                feature = MetricFeature(
                    normalized_metric_id=metric.id,
                    feature_key=definition.primary_feature_key,
                    feature_payload=payload,
                )
                session.add(feature)
                existing_features[metric.id] = feature
            else:
                feature.feature_key = definition.primary_feature_key
                feature.feature_payload = payload
            written += 1

    session.flush()
    return FeaturePipelineResult(metric_features_written=written)
