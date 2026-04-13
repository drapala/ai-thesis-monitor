"""Weekly score ingestion glue."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import delete, desc, select
from sqlalchemy.orm import Session

from ai_thesis_monitor.db.models.analytics import (
    Alert,
    Claim,
    ModuleScore,
    NarrativeSnapshot,
    NormalizedMetric,
    ScoreEvidence,
    TripwireEvent,
)
from ai_thesis_monitor.db.models.core import MetricDefinition
from ai_thesis_monitor.domain.narratives.build import build_weekly_summary
from ai_thesis_monitor.domain.scoring.aggregation import ModuleScoreResult, aggregate_module_score
from ai_thesis_monitor.domain.scoring.evidence import EvidenceRecord
from ai_thesis_monitor.domain.tripwires.detect import TripwireResult, detect_tripwires

THREE_DECIMALS = Decimal("0.001")


@dataclass(frozen=True)
class WeeklyPipelineResult:
    module_scores_written: int
    tripwires_written: int
    alerts_written: int
    narratives_written: int


def run_weekly_pipeline(*, session: Session, score_date: date) -> WeeklyPipelineResult:
    _clear_score_date_materializations(session, score_date)

    claims_window_start = score_date - timedelta(days=6)
    metric_evidence = _load_metric_evidence(session, score_date)
    claim_rows = _load_claim_rows(session, claims_window_start, score_date)

    evidence_by_module: dict[str, list[EvidenceRecord]] = {}
    recent_claims: dict[str, list[Claim]] = {}

    for evidence in metric_evidence:
        evidence_by_module.setdefault(evidence.module_key, []).append(evidence)
    for claim in claim_rows:
        evidence = _claim_to_evidence(claim)
        evidence_by_module.setdefault(evidence.module_key, []).append(evidence)
        recent_claims.setdefault(claim.module_key, []).append(claim)

    score_evidence_rows: list[ScoreEvidence] = []
    module_score_rows: list[ModuleScore] = []
    tripwire_rows: list[TripwireEvent] = []
    alert_rows: list[Alert] = []
    module_scores: list[ModuleScoreResult] = []
    module_regimes: dict[str, str] = {}

    for module_key in sorted(evidence_by_module):
        evidence = evidence_by_module[module_key]
        for row in evidence:
            score_evidence_rows.append(
                ScoreEvidence(
                    module_key=row.module_key,
                    score_date=score_date,
                    evidence_type=row.evidence_type,
                    bucket_key=row.bucket_key,
                    direction=row.direction,
                    strength=row.strength,
                    impact=row.impact,
                    weight=row.weight,
                    quality=row.quality,
                    contribution_citadel=row.contribution_citadel,
                    contribution_citrini=row.contribution_citrini,
                    explanation=row.explanation,
                    references=row.references,
                )
            )

        score = aggregate_module_score(module_key, evidence)
        winning_thesis = _winning_thesis(score)
        module_score_rows.append(
            ModuleScore(
                module_key=module_key,
                score_date=score_date,
                score_citadel=score.score_citadel,
                score_citrini=score.score_citrini,
                confidence=score.confidence,
                winning_thesis=winning_thesis,
                regime=score.regime,
                explanation=_module_score_explanation(score, evidence),
            )
        )
        module_scores.append(score)
        module_regimes[module_key] = score.regime

        history = session.scalars(
            select(ModuleScore)
            .where(
                ModuleScore.module_key == module_key,
                ModuleScore.score_date < score_date,
            )
            .order_by(desc(ModuleScore.score_date))
            .limit(2)
        ).all()
        history.reverse()
        consecutive_history = _consecutive_weekly_history(history, score_date)

        detected = detect_tripwires(
            module_key=module_key,
            score_dates=[*map(lambda row: row.score_date, consecutive_history), score_date],
            regimes=[*map(lambda row: row.regime, consecutive_history), score.regime],
            critical_claims=[claim.claim_text for claim in recent_claims.get(module_key, [])],
        )
        for tripwire in detected:
            title = _tripwire_title(tripwire)
            description = _tripwire_description(tripwire)
            tripwire_rows.append(
                TripwireEvent(
                    module_key=module_key,
                    tripwire_key=tripwire.tripwire_key,
                    title=title,
                    description=description,
                    direction=tripwire.direction,
                    severity=tripwire.severity,
                    trigger_type=tripwire.trigger_type,
                    event_date=tripwire.event_date,
                    valid_until=tripwire.valid_until,
                    decay_factor=_quantize(Decimal(str(tripwire.decay_factor))),
                    evidence_refs={
                        "score_date": score_date.isoformat(),
                        "claim_ids": [str(claim.id) for claim in recent_claims.get(module_key, [])],
                    },
                    review_status="not_required",
                )
            )
            alert_rows.append(
                Alert(
                    alert_key=f"weekly:{tripwire.tripwire_key}:{score_date.isoformat()}",
                    module_key=module_key,
                    severity=tripwire.severity,
                    title=title,
                    message=description,
                    triggered_at=_score_date_timestamp(score_date),
                    status="open",
                )
            )

    overall_winner, overall_confidence = _overall_outcome(module_scores)
    narrative = NarrativeSnapshot(
        snapshot_date=score_date,
        overall_winner=overall_winner,
        confidence=overall_confidence,
        summary=build_weekly_summary(
            overall_winner=overall_winner,
            module_regimes=module_regimes,
            new_evidence=_new_evidence_lines(evidence_by_module),
            open_questions=_open_questions(recent_claims),
        ),
        module_breakdown={
            score.module_key: {
                "winning_thesis": _winning_thesis(score),
                "regime": score.regime,
                "confidence": str(score.confidence),
            }
            for score in module_scores
        },
        supporting_evidence={
            module_key: [evidence.references for evidence in evidence_rows[:3]]
            for module_key, evidence_rows in evidence_by_module.items()
        },
    )

    session.add_all(score_evidence_rows)
    session.add_all(module_score_rows)
    session.add_all(tripwire_rows)
    session.add_all(alert_rows)
    session.add(narrative)
    session.flush()

    return WeeklyPipelineResult(
        module_scores_written=len(module_score_rows),
        tripwires_written=len(tripwire_rows),
        alerts_written=len(alert_rows),
        narratives_written=1,
    )


def _clear_score_date_materializations(session: Session, score_date: date) -> None:
    session.execute(delete(ScoreEvidence).where(ScoreEvidence.score_date == score_date))
    session.execute(delete(ModuleScore).where(ModuleScore.score_date == score_date))
    session.execute(delete(TripwireEvent).where(TripwireEvent.event_date == score_date))
    day_start = _score_date_timestamp(score_date)
    session.execute(
        delete(Alert).where(
            Alert.alert_key.like("weekly:%"),
            Alert.triggered_at >= day_start,
            Alert.triggered_at < day_start + timedelta(days=1),
        )
    )
    session.execute(delete(NarrativeSnapshot).where(NarrativeSnapshot.snapshot_date == score_date))


def _load_metric_evidence(session: Session, score_date: date) -> list[EvidenceRecord]:
    metric_rows = session.execute(
        select(NormalizedMetric, MetricDefinition)
        .join(MetricDefinition, MetricDefinition.id == NormalizedMetric.metric_definition_id)
        .where(
            NormalizedMetric.observed_date <= score_date,
            MetricDefinition.is_active.is_(True),
        )
        .order_by(
            NormalizedMetric.metric_definition_id,
            NormalizedMetric.source_id,
            NormalizedMetric.geo,
            NormalizedMetric.segment,
            desc(NormalizedMetric.observed_date),
            desc(NormalizedMetric.id),
        )
    ).all()

    latest_rows: dict[tuple[int, int, str | None, str | None], tuple[NormalizedMetric, MetricDefinition]] = {}
    for metric, definition in metric_rows:
        semantic_key = (metric.metric_definition_id, metric.source_id, metric.geo, metric.segment)
        latest_rows.setdefault(semantic_key, (metric, definition))

    evidence: list[EvidenceRecord] = []
    for metric, definition in latest_rows.values():
        row = _metric_to_evidence(metric, definition)
        if row is not None:
            evidence.append(row)
    return evidence


def _load_claim_rows(session: Session, window_start: date, score_date: date) -> list[Claim]:
    claims = session.scalars(select(Claim).order_by(Claim.id)).all()
    return [
        claim
        for claim in claims
        if (effective_date := _claim_effective_date(claim)) is not None and window_start <= effective_date <= score_date
    ]


def _metric_to_evidence(
    metric: NormalizedMetric, definition: MetricDefinition
) -> EvidenceRecord | None:
    value = Decimal(metric.value)
    strength = min(abs(value), Decimal("1.000"))
    if strength == 0:
        return None

    direction = _metric_direction(value=value, expected_direction_citadel=definition.expected_direction_citadel)
    impact = Decimal("1.000")
    weight = _quantize(Decimal(str(definition.weight)))
    quality = _quantize(Decimal(metric.quality_score))
    contribution = _quantize(strength * impact * weight * quality)
    contribution_citadel = Decimal("0.000")
    contribution_citrini = Decimal("0.000")

    if direction == "citadel":
        contribution_citadel = contribution
    elif direction == "citrini":
        contribution_citrini = contribution

    return EvidenceRecord(
        module_key=definition.module_key,
        evidence_type="metric",
        bucket_key=definition.metric_key,
        direction=direction,
        strength=_quantize(strength),
        impact=impact,
        weight=weight,
        quality=quality,
        contribution_citadel=contribution_citadel,
        contribution_citrini=contribution_citrini,
        explanation=(
            f"{definition.metric_key} recorded {value} on {metric.observed_date.isoformat()} "
            f"for module {definition.module_key}"
        ),
        references={
            "normalized_metric_id": str(metric.id),
            "metric_definition_id": str(definition.id),
        },
    )


def _claim_to_evidence(claim: Claim) -> EvidenceRecord:
    direction = claim.evidence_direction if claim.evidence_direction in {"citadel", "citrini"} else "neutral"
    strength = _quantize(Decimal(claim.strength))
    quality = _quantize(Decimal(claim.confidence))
    contribution = _quantize(strength * quality)
    contribution_citadel = Decimal("0.000")
    contribution_citrini = Decimal("0.000")
    if direction == "citadel":
        contribution_citadel = contribution
    elif direction == "citrini":
        contribution_citrini = contribution

    return EvidenceRecord(
        module_key=claim.module_key,
        evidence_type="claim",
        bucket_key=claim.claim_type,
        direction=direction,
        strength=strength,
        impact=Decimal("1.000"),
        weight=Decimal("1.000"),
        quality=quality,
        contribution_citadel=contribution_citadel,
        contribution_citrini=contribution_citrini,
        explanation=claim.claim_text,
        references={"claim_id": str(claim.id)},
    )


def _metric_direction(*, value: Decimal, expected_direction_citadel: str) -> str:
    if value == 0 or expected_direction_citadel == "neutral":
        return "neutral"
    if expected_direction_citadel not in {"up", "down"}:
        return "neutral"

    if value > 0:
        return "citadel" if expected_direction_citadel == "up" else "citrini"
    return "citadel" if expected_direction_citadel == "down" else "citrini"


def _claim_effective_date(claim: Claim) -> date | None:
    return claim.evidence_date or claim.published_date


def _winning_thesis(score: ModuleScoreResult) -> str:
    if score.score_citadel > score.score_citrini:
        return "citadel"
    if score.score_citrini > score.score_citadel:
        return "citrini"
    return "neutral"


def _module_score_explanation(score: ModuleScoreResult, evidence: list[EvidenceRecord]) -> str:
    primary = evidence[0].explanation if evidence else "no evidence"
    return (
        f"{score.module_key} scored {score.score_citadel} for citadel and {score.score_citrini} for citrini; "
        f"regime {score.regime}. Lead evidence: {primary}"
    )


def _tripwire_title(tripwire: TripwireResult) -> str:
    return tripwire.tripwire_key.replace("_", " ").title()


def _tripwire_description(tripwire: TripwireResult) -> str:
    return (
        f"{tripwire.module_key} triggered a {tripwire.trigger_type} tripwire "
        f"favoring {tripwire.direction} on {tripwire.event_date.isoformat()}."
    )


def _overall_outcome(module_scores: list[ModuleScoreResult]) -> tuple[str, Decimal]:
    total_citadel = sum((score.score_citadel for score in module_scores), start=Decimal("0.000"))
    total_citrini = sum((score.score_citrini for score in module_scores), start=Decimal("0.000"))
    confidence_values = [score.confidence for score in module_scores]

    if total_citadel > total_citrini:
        winner = "citadel"
    elif total_citrini > total_citadel:
        winner = "citrini"
    else:
        winner = "neutral"

    confidence = max(confidence_values, default=Decimal("0.500"))
    return winner, _quantize(confidence)


def _new_evidence_lines(evidence_by_module: dict[str, list[EvidenceRecord]]) -> list[str]:
    lines: list[str] = []
    for evidence_rows in evidence_by_module.values():
        for row in evidence_rows[:2]:
            lines.append(row.explanation)
    return lines


def _open_questions(recent_claims: dict[str, list[Claim]]) -> list[str]:
    questions: list[str] = []
    for claims in recent_claims.values():
        for claim in claims:
            if claim.review_status != "not_required":
                questions.append(f"review claim {claim.id} for module {claim.module_key}")
    return questions


def _consecutive_weekly_history(history: list[ModuleScore], score_date: date) -> list[ModuleScore]:
    if not history:
        return []

    expected_date = score_date - timedelta(days=7)
    consecutive: list[ModuleScore] = []
    for row in reversed(history):
        if row.score_date != expected_date:
            if row.score_date < expected_date:
                break
            continue
        consecutive.append(row)
        expected_date -= timedelta(days=7)

    consecutive.reverse()
    return consecutive


def _score_date_timestamp(score_date: date) -> datetime:
    return datetime.combine(score_date, time.min, tzinfo=timezone.utc)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(THREE_DECIMALS, rounding=ROUND_HALF_UP)
