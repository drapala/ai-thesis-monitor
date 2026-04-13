"""Analytics persistence models for metrics, evidence, scoring, and narratives."""

from __future__ import annotations

from decimal import Decimal
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from ai_thesis_monitor.db.models.base import Base


class NormalizedMetric(Base):
    __tablename__ = "normalized_metrics"
    __table_args__ = (
        UniqueConstraint(
            "metric_definition_id",
            "source_id",
            "observed_date",
            "geo",
            "segment",
            name="uq_normalized_metric_semantic_key",
            postgresql_nulls_not_distinct=True,
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    metric_definition_id: Mapped[int] = mapped_column(ForeignKey("metric_definitions.id"), nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)
    raw_observation_id: Mapped[int | None] = mapped_column(ForeignKey("raw_observations.id"), nullable=True)
    geo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    segment: Mapped[str | None] = mapped_column(String(255), nullable=True)
    observed_date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    quality_score: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False, server_default="0.800")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class MetricFeature(Base):
    __tablename__ = "metric_features"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    normalized_metric_id: Mapped[int] = mapped_column(
        ForeignKey("normalized_metrics.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    feature_key: Mapped[str] = mapped_column(String(255), nullable=False)
    feature_payload: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)
    raw_observation_id: Mapped[int] = mapped_column(ForeignKey("raw_observations.id"), nullable=False)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False)
    chunk_id: Mapped[int] = mapped_column(ForeignKey("document_chunks.id"), nullable=False)
    module_key: Mapped[str] = mapped_column(String(255), nullable=False)
    claim_type: Mapped[str] = mapped_column(String(255), nullable=False)
    entity: Mapped[str | None] = mapped_column(String(255), nullable=True)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_direction: Mapped[str] = mapped_column(String(64), nullable=False)
    strength: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    evidence_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    published_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    dedupe_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    review_status: Mapped[str] = mapped_column(String(64), nullable=False, server_default="not_required")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ScoreEvidence(Base):
    __tablename__ = "score_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    module_key: Mapped[str] = mapped_column(String(255), nullable=False)
    score_date: Mapped[date] = mapped_column(Date, nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    bucket_key: Mapped[str] = mapped_column(String(255), nullable=False)
    direction: Mapped[str] = mapped_column(String(32), nullable=False)
    strength: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    impact: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    quality: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    contribution_citadel: Mapped[Decimal] = mapped_column(Numeric(8, 3), nullable=False)
    contribution_citrini: Mapped[Decimal] = mapped_column(Numeric(8, 3), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    references: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ModuleScore(Base):
    __tablename__ = "module_scores"
    __table_args__ = (UniqueConstraint("module_key", "score_date", name="uq_module_scores"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    module_key: Mapped[str] = mapped_column(String(255), nullable=False)
    score_date: Mapped[date] = mapped_column(Date, nullable=False)
    score_citadel: Mapped[Decimal] = mapped_column(Numeric(8, 3), nullable=False)
    score_citrini: Mapped[Decimal] = mapped_column(Numeric(8, 3), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    winning_thesis: Mapped[str] = mapped_column(String(64), nullable=False)
    regime: Mapped[str] = mapped_column(String(64), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class TripwireEvent(Base):
    __tablename__ = "tripwire_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    module_key: Mapped[str] = mapped_column(String(255), nullable=False)
    tripwire_key: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    direction: Mapped[str] = mapped_column(String(32), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(64), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    decay_factor: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False, server_default="1.000")
    evidence_refs: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")
    review_status: Mapped[str] = mapped_column(String(64), nullable=False, server_default="not_required")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_key: Mapped[str] = mapped_column(String(255), nullable=False)
    module_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="open")


class NarrativeSnapshot(Base):
    __tablename__ = "narrative_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    overall_winner: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    module_breakdown: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")
    supporting_evidence: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
