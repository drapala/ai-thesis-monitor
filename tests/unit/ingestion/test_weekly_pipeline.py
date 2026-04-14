from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, Session as OrmSession

from ai_thesis_monitor.db.models.analytics import (
    Alert,
    Claim,
    MetricFeature,
    ModuleScore,
    NarrativeSnapshot,
    NormalizedMetric,
    ScoreEvidence,
    TripwireEvent,
)
from ai_thesis_monitor.db.models.core import Document, DocumentChunk, MetricDefinition, RawObservation, Source
from ai_thesis_monitor.ingestion.pipelines.weekly import run_weekly_pipeline


@pytest.fixture(autouse=True)
def clean_weekly_tables(db_session: Session) -> None:
    db_session.execute(delete(Alert))
    db_session.execute(delete(TripwireEvent))
    db_session.execute(delete(NarrativeSnapshot))
    db_session.execute(delete(ModuleScore))
    db_session.execute(delete(ScoreEvidence))
    db_session.execute(delete(Claim))
    db_session.execute(delete(DocumentChunk))
    db_session.execute(delete(Document))
    db_session.execute(delete(MetricFeature))
    db_session.execute(delete(NormalizedMetric))
    db_session.execute(delete(RawObservation))
    db_session.execute(delete(MetricDefinition))
    db_session.execute(delete(Source))
    db_session.commit()
    yield
    db_session.execute(delete(Alert))
    db_session.execute(delete(TripwireEvent))
    db_session.execute(delete(NarrativeSnapshot))
    db_session.execute(delete(ModuleScore))
    db_session.execute(delete(ScoreEvidence))
    db_session.execute(delete(Claim))
    db_session.execute(delete(DocumentChunk))
    db_session.execute(delete(Document))
    db_session.execute(delete(MetricFeature))
    db_session.execute(delete(NormalizedMetric))
    db_session.execute(delete(RawObservation))
    db_session.execute(delete(MetricDefinition))
    db_session.execute(delete(Source))
    db_session.commit()


def test_run_weekly_pipeline_persists_outputs_for_explicit_score_date(db_session: Session) -> None:
    score_date = date(2026, 4, 6)
    _seed_weekly_inputs(db_session, score_date=score_date)

    result = run_weekly_pipeline(session=db_session, score_date=score_date)

    assert result.module_scores_written == 1
    assert result.tripwires_written == 1
    assert result.alerts_written == 1
    assert result.narratives_written == 1

    assert db_session.scalar(select(func.count()).select_from(ScoreEvidence)) == 2
    assert db_session.scalar(select(func.count()).select_from(ModuleScore)) == 1
    assert db_session.scalar(select(func.count()).select_from(TripwireEvent)) == 1
    assert db_session.scalar(select(func.count()).select_from(Alert)) == 1
    assert db_session.scalar(select(func.count()).select_from(NarrativeSnapshot)) == 1

    module_score = db_session.scalar(select(ModuleScore))
    assert module_score is not None
    assert module_score.module_key == "labor"
    assert module_score.score_date == score_date
    assert module_score.winning_thesis == "citrini"

    tripwire = db_session.scalar(select(TripwireEvent))
    assert tripwire is not None
    assert tripwire.tripwire_key == "labor_critical_claim"
    assert tripwire.event_date == score_date

    narrative = db_session.scalar(select(NarrativeSnapshot))
    assert narrative is not None
    assert narrative.snapshot_date == score_date
    assert narrative.overall_winner == "citrini"

    db_session.commit()
    persisted = OrmSession(bind=db_session.get_bind())
    try:
        assert persisted.scalar(select(func.count()).select_from(ScoreEvidence)) == 2
        assert persisted.scalar(select(func.count()).select_from(ModuleScore)) == 1
        assert persisted.scalar(select(func.count()).select_from(TripwireEvent)) == 1
        assert persisted.scalar(select(func.count()).select_from(Alert)) == 1
        stored_narrative = persisted.scalar(select(NarrativeSnapshot))
        assert stored_narrative is not None
        assert stored_narrative.snapshot_date == score_date
    finally:
        persisted.close()

    rerun = run_weekly_pipeline(session=db_session, score_date=score_date)

    assert rerun == result
    assert db_session.scalar(select(func.count()).select_from(ScoreEvidence)) == 2
    assert db_session.scalar(select(func.count()).select_from(ModuleScore)) == 1
    assert db_session.scalar(select(func.count()).select_from(TripwireEvent)) == 1
    assert db_session.scalar(select(func.count()).select_from(Alert)) == 1
    assert db_session.scalar(select(func.count()).select_from(NarrativeSnapshot)) == 1


def test_run_weekly_pipeline_requires_consecutive_weeks_for_persistent_deterioration_tripwire(
    db_session: Session,
) -> None:
    score_date = date(2026, 4, 6)
    _seed_weekly_inputs(db_session, score_date=score_date)
    db_session.add_all(
        [
            ModuleScore(
                module_key="labor",
                score_date=date(2026, 3, 9),
                score_citadel=Decimal("0.000"),
                score_citrini=Decimal("0.800"),
                confidence=Decimal("0.700"),
                winning_thesis="citrini",
                regime="leaning_citrini",
                explanation="historical weekly score",
            ),
            ModuleScore(
                module_key="labor",
                score_date=date(2026, 3, 23),
                score_citadel=Decimal("0.000"),
                score_citrini=Decimal("0.900"),
                confidence=Decimal("0.750"),
                winning_thesis="citrini",
                regime="leaning_citrini",
                explanation="historical weekly score",
            ),
        ]
    )
    db_session.commit()

    result = run_weekly_pipeline(session=db_session, score_date=score_date)

    assert result.tripwires_written == 1
    tripwire_keys = set(db_session.scalars(select(TripwireEvent.tripwire_key)))
    assert "labor_critical_claim" in tripwire_keys
    assert "labor_persistent_deterioration_3w" not in tripwire_keys


def test_run_weekly_pipeline_excludes_rejected_claims_from_evidence_and_tripwires(db_session: Session) -> None:
    score_date = date(2026, 4, 6)
    _seed_weekly_inputs(db_session, score_date=score_date)

    initial = run_weekly_pipeline(session=db_session, score_date=score_date)

    assert initial.module_scores_written == 1
    assert initial.tripwires_written == 1
    assert db_session.scalar(
        select(func.count()).select_from(ScoreEvidence).where(ScoreEvidence.evidence_type == "claim")
    ) == 1

    claim = db_session.scalar(select(Claim).where(Claim.dedupe_key == "weekly-unit-claim"))
    assert claim is not None
    claim.review_status = "rejected"
    db_session.commit()

    rerun = run_weekly_pipeline(session=db_session, score_date=score_date)

    assert rerun.module_scores_written == 1
    assert rerun.tripwires_written == 0
    assert rerun.alerts_written == 0
    assert db_session.scalar(
        select(func.count()).select_from(ScoreEvidence).where(ScoreEvidence.evidence_type == "claim")
    ) == 0
    assert db_session.scalar(select(func.count()).select_from(TripwireEvent)) == 0

    narrative = db_session.scalar(select(NarrativeSnapshot).where(NarrativeSnapshot.snapshot_date == score_date))
    assert narrative is not None
    assert "review claim" not in narrative.summary
    assert "no open questions" in narrative.summary


def test_run_weekly_pipeline_keeps_pending_claims_open_but_closes_approved_ones(db_session: Session) -> None:
    score_date = date(2026, 4, 6)
    _seed_weekly_inputs(db_session, score_date=score_date)

    run_weekly_pipeline(session=db_session, score_date=score_date)

    claim = db_session.scalar(select(Claim).where(Claim.dedupe_key == "weekly-unit-claim"))
    assert claim is not None
    narrative = db_session.scalar(select(NarrativeSnapshot).where(NarrativeSnapshot.snapshot_date == score_date))
    assert narrative is not None
    assert f"review claim {claim.id} for module labor" in narrative.summary

    claim.review_status = "approved"
    db_session.commit()

    rerun = run_weekly_pipeline(session=db_session, score_date=score_date)

    assert rerun.module_scores_written == 1
    updated_narrative = db_session.scalar(select(NarrativeSnapshot).where(NarrativeSnapshot.snapshot_date == score_date))
    assert updated_narrative is not None
    assert f"review claim {claim.id} for module labor" not in updated_narrative.summary
    assert "no open questions" in updated_narrative.summary


def test_run_weekly_pipeline_reduces_pending_review_claim_weight_vs_approved(db_session: Session) -> None:
    score_date = date(2026, 4, 6)
    _seed_weekly_inputs(db_session, score_date=score_date)

    run_weekly_pipeline(session=db_session, score_date=score_date)

    pending_claim_evidence = db_session.scalar(
        select(ScoreEvidence)
        .where(ScoreEvidence.score_date == score_date, ScoreEvidence.evidence_type == "claim")
        .order_by(ScoreEvidence.id.desc())
    )
    pending_module_score = db_session.scalar(select(ModuleScore).where(ModuleScore.score_date == score_date))
    assert pending_claim_evidence is not None
    assert pending_module_score is not None
    pending_contribution_citrini = pending_claim_evidence.contribution_citrini
    pending_weight = pending_claim_evidence.weight
    pending_score_citrini = pending_module_score.score_citrini

    claim = db_session.scalar(select(Claim).where(Claim.dedupe_key == "weekly-unit-claim"))
    assert claim is not None
    claim.review_status = "approved"
    db_session.commit()

    run_weekly_pipeline(session=db_session, score_date=score_date)

    approved_claim_evidence = db_session.scalar(
        select(ScoreEvidence)
        .where(ScoreEvidence.score_date == score_date, ScoreEvidence.evidence_type == "claim")
        .order_by(ScoreEvidence.id.desc())
    )
    approved_module_score = db_session.scalar(select(ModuleScore).where(ModuleScore.score_date == score_date))
    assert approved_claim_evidence is not None
    assert approved_module_score is not None

    assert pending_contribution_citrini == Decimal("0.383")
    assert approved_claim_evidence.contribution_citrini == Decimal("0.765")
    assert pending_weight == Decimal("0.500")
    assert approved_claim_evidence.weight == Decimal("1.000")
    assert approved_module_score.score_citrini > pending_score_citrini


def test_run_weekly_pipeline_uses_primary_feature_instead_of_raw_level(db_session: Session) -> None:
    score_date = date(2026, 4, 6)
    source = Source(
        source_key="weekly_productivity_source",
        source_name="Weekly Productivity Source",
        source_type="test",
        base_url="https://example.test/productivity",
        config={},
        reliability_score=0.90,
        active=True,
    )
    metric_definition = MetricDefinition(
        metric_key="labor_productivity_yoy",
        module_key="productivity",
        name="Labor Productivity YoY",
        description="Synthetic quarterly productivity series",
        frequency="quarterly",
        unit="percent",
        lag_category="confirmatory",
        weight=1.2,
        expected_direction_citadel="up",
        expected_direction_citrini="up",
        primary_feature_key="yoy",
        signal_transform="higher_is_citadel",
        min_history_points=4,
        is_leading=False,
        config={},
        is_active=True,
    )
    db_session.add(source)
    db_session.add(metric_definition)
    db_session.flush()

    quarterly_values = [
        (date(2025, 4, 1), Decimal("100.0")),
        (date(2025, 7, 1), Decimal("102.0")),
        (date(2025, 10, 1), Decimal("101.0")),
        (date(2026, 1, 1), Decimal("100.0")),
        (score_date, Decimal("95.0")),
    ]

    for index, (observed_date, value) in enumerate(quarterly_values, start=1):
        raw_observation = RawObservation(
            source_id=source.id,
            external_id=f"productivity-{index}",
            payload={"observed_date": observed_date.isoformat(), "value": str(value)},
            content_hash=f"productivity-{index}",
            published_at=datetime.combine(observed_date, datetime.min.time(), tzinfo=timezone.utc),
        )
        db_session.add(raw_observation)
        db_session.flush()
        db_session.add(
            NormalizedMetric(
                metric_definition_id=metric_definition.id,
                source_id=source.id,
                raw_observation_id=raw_observation.id,
                observed_date=observed_date,
                value=value,
                quality_score=Decimal("0.900"),
            )
        )
    db_session.commit()

    result = run_weekly_pipeline(session=db_session, score_date=score_date)

    assert result.module_scores_written >= 1
    module_score = db_session.scalar(
        select(ModuleScore).where(
            ModuleScore.score_date == score_date,
            ModuleScore.module_key == "productivity",
        )
    )
    assert module_score is not None
    assert module_score.module_key == "productivity"
    assert module_score.winning_thesis == "citrini"

    score_evidence = db_session.scalar(
        select(ScoreEvidence).where(
            ScoreEvidence.score_date == score_date,
            ScoreEvidence.module_key == "productivity",
        )
    )
    assert score_evidence is not None
    assert score_evidence.bucket_key == "labor_productivity_yoy"
    assert score_evidence.direction == "citrini"
    assert "using yoy" in score_evidence.explanation


def _seed_weekly_inputs(db_session: Session, *, score_date: date) -> None:
    source = Source(
        source_key="weekly_unit_source",
        source_name="Weekly Unit Source",
        source_type="test",
        base_url="https://example.test/weekly",
        config={},
        reliability_score=0.82,
        active=True,
    )
    metric_definition = MetricDefinition(
        metric_key="software_postings_yoy",
        module_key="labor",
        name="Software Job Postings YoY",
        description="Synthetic test metric for weekly scoring",
        frequency="weekly",
        unit="index",
        lag_category="short",
        weight=1.2,
        expected_direction_citadel="up",
        expected_direction_citrini="down",
        primary_feature_key="value",
        signal_transform="identity",
        min_history_points=1,
        is_leading=True,
        config={},
        is_active=True,
    )
    db_session.add(source)
    db_session.add(metric_definition)
    db_session.flush()

    raw_observation = RawObservation(
        source_id=source.id,
        external_id="weekly-unit-raw",
        payload={"kind": "weekly"},
        content_hash="weekly-unit-raw",
        published_at=datetime(2026, 4, 5, tzinfo=timezone.utc),
    )
    db_session.add(raw_observation)
    db_session.flush()

    document = Document(
        source_id=source.id,
        raw_observation_id=raw_observation.id,
        title="Weekly labor evidence",
        url="https://example.test/weekly/labor",
        body_text="Synthetic weekly evidence body",
        published_at=raw_observation.published_at,
    )
    db_session.add(document)
    db_session.flush()

    chunk = DocumentChunk(
        document_id=document.id,
        chunk_index=0,
        chunk_text="Synthetic weekly evidence chunk",
        chunk_hash="weekly-unit-chunk",
    )
    db_session.add(chunk)
    db_session.flush()

    db_session.add(
        NormalizedMetric(
            metric_definition_id=metric_definition.id,
            source_id=source.id,
            raw_observation_id=raw_observation.id,
            geo=None,
            segment=None,
            observed_date=score_date,
            value=Decimal("-0.900"),
            quality_score=Decimal("0.850"),
            notes="Negative normalized trend for labor",
        )
    )
    db_session.add(
        Claim(
            source_id=source.id,
            raw_observation_id=raw_observation.id,
            document_id=document.id,
            chunk_id=chunk.id,
            module_key="labor",
            claim_type="headcount_reduction_ai_efficiency",
            entity="Example Co",
            claim_text="Example Co said AI efficiency reduced labor demand.",
            evidence_direction="citrini",
            strength=Decimal("0.900"),
            confidence=Decimal("0.850"),
            evidence_date=score_date,
            published_date=score_date,
            dedupe_key="weekly-unit-claim",
            review_status="pending_review",
        )
    )
    db_session.commit()
