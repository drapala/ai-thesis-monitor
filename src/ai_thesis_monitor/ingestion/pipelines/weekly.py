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
    MetricFeature,
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
from ai_thesis_monitor.ingestion.pipelines.features import run_feature_pipeline

THREE_DECIMALS = Decimal("0.001")
OPEN_QUESTION_REVIEW_STATUSES = {"pending_review"}
WEEKLY_EVIDENCE_REVIEW_STATUSES = {"pending_review", "approved", "not_required"}
PENDING_REVIEW_CLAIM_WEIGHT = Decimal("0.500")


@dataclass(frozen=True)
class WeeklyPipelineResult:
    module_scores_written: int
    tripwires_written: int
    alerts_written: int
    narratives_written: int


def run_weekly_pipeline(*, session: Session, score_date: date) -> WeeklyPipelineResult:
    run_feature_pipeline(session, observed_date_lte=score_date)
    _clear_score_date_materializations(session, score_date)

    claims_window_start = score_date - timedelta(days=6)
    metric_evidence = _load_metric_evidence(session, score_date)
    claim_rows = _load_claim_rows(session, claims_window_start, score_date)

    evidence_by_module: dict[str, list[EvidenceRecord]] = {}
    recent_claims: dict[str, list[Claim]] = {}

    for evidence_row in metric_evidence:
        evidence_by_module.setdefault(evidence_row.module_key, []).append(evidence_row)
    for claim in claim_rows:
        claim_evidence = _claim_to_evidence(claim)
        evidence_by_module.setdefault(claim_evidence.module_key, []).append(claim_evidence)
        recent_claims.setdefault(claim.module_key, []).append(claim)

    score_evidence_rows: list[ScoreEvidence] = []
    module_score_rows: list[ModuleScore] = []
    tripwire_rows: list[TripwireEvent] = []
    alert_rows: list[Alert] = []
    module_scores: list[ModuleScoreResult] = []
    module_regimes: dict[str, str] = {}

    for module_key in sorted(evidence_by_module):
        module_evidence = evidence_by_module[module_key]
        for row in module_evidence:
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

        score = aggregate_module_score(module_key, module_evidence)
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
                explanation=_module_score_explanation(score, module_evidence),
            )
        )
        module_scores.append(score)
        module_regimes[module_key] = score.regime

        history = list(
            session.scalars(
            select(ModuleScore)
            .where(
                ModuleScore.module_key == module_key,
                ModuleScore.score_date < score_date,
            )
            .order_by(desc(ModuleScore.score_date))
            .limit(2)
        ).all()
        )
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
        select(NormalizedMetric, MetricDefinition, MetricFeature)
        .join(MetricDefinition, MetricDefinition.id == NormalizedMetric.metric_definition_id)
        .outerjoin(MetricFeature, MetricFeature.normalized_metric_id == NormalizedMetric.id)
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

    latest_rows: dict[
        tuple[int, int, str | None, str | None], tuple[NormalizedMetric, MetricDefinition, MetricFeature | None]
    ] = {}
    for metric, definition, feature in metric_rows:
        semantic_key = (metric.metric_definition_id, metric.source_id, metric.geo, metric.segment)
        latest_rows.setdefault(semantic_key, (metric, definition, feature))

    evidence: list[EvidenceRecord] = []
    for metric, definition, feature in latest_rows.values():
        row = _metric_to_evidence(metric, definition, feature)
        if row is not None:
            evidence.append(row)
    return evidence


def _load_claim_rows(session: Session, window_start: date, score_date: date) -> list[Claim]:
    claims = session.scalars(select(Claim).order_by(Claim.id)).all()
    return [
        claim
        for claim in claims
        if (
            claim.review_status in WEEKLY_EVIDENCE_REVIEW_STATUSES
            and (effective_date := _claim_effective_date(claim)) is not None
            and window_start <= effective_date <= score_date
        )
    ]


def _metric_to_evidence(
    metric: NormalizedMetric, definition: MetricDefinition, feature: MetricFeature | None
) -> EvidenceRecord | None:
    feature_payload = feature.feature_payload if feature is not None else {}
    history_points = int(feature_payload.get("history_points", 0) or 0)
    if history_points < definition.min_history_points:
        return None

    feature_key = definition.primary_feature_key
    feature_value = feature_payload.get(feature_key)
    scalar = _feature_scalar(feature_value)
    strength = _feature_strength(feature_payload, feature_key, scalar)
    if definition.signal_transform != "adoption_only" and strength == 0:
        return None

    direction = _metric_direction_from_transform(
        scalar=scalar,
        signal_transform=definition.signal_transform,
        expected_direction_citadel=definition.expected_direction_citadel,
    )
    impact = Decimal("1.000")
    weight = _quantize(Decimal(str(definition.weight)))
    quality = _quantize(Decimal(metric.quality_score))
    contribution = _quantize(strength * impact * weight * quality)
    contribution_citadel = Decimal("0.000")
    contribution_citrini = Decimal("0.000")

    if definition.signal_transform == "adoption_only":
        half_contribution = _quantize(contribution / Decimal("2"))
        contribution_citadel = half_contribution
        contribution_citrini = half_contribution
    elif direction == "citadel":
        contribution_citadel = contribution
    elif direction == "citrini":
        contribution_citrini = contribution

    references = {
        "normalized_metric_id": str(metric.id),
        "metric_definition_id": str(definition.id),
    }
    if feature is not None:
        references["metric_feature_id"] = str(feature.id)

    return EvidenceRecord(
        module_key=definition.module_key,
        evidence_type="metric",
        bucket_key=definition.metric_key,
        direction=direction,
        strength=strength,
        impact=impact,
        weight=weight,
        quality=quality,
        contribution_citadel=contribution_citadel,
        contribution_citrini=contribution_citrini,
        explanation=(
            f"{definition.metric_key} using {feature_key}={feature_value} on {metric.observed_date.isoformat()} "
            f"for module {definition.module_key}"
        ),
        references=references,
    )


def _claim_to_evidence(claim: Claim) -> EvidenceRecord:
    direction = claim.evidence_direction if claim.evidence_direction in {"citadel", "citrini"} else "neutral"
    strength = _quantize(Decimal(claim.strength))
    weight = _claim_evidence_weight(claim.review_status)
    quality = _quantize(Decimal(claim.confidence))
    contribution = _quantize(strength * quality * weight)
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
        weight=weight,
        quality=quality,
        contribution_citadel=contribution_citadel,
        contribution_citrini=contribution_citrini,
        explanation=claim.claim_text,
        references={"claim_id": str(claim.id)},
    )


def _claim_evidence_weight(review_status: str) -> Decimal:
    if review_status == "pending_review":
        return PENDING_REVIEW_CLAIM_WEIGHT
    return Decimal("1.000")


def _metric_direction_from_transform(
    *,
    scalar: Decimal,
    signal_transform: str,
    expected_direction_citadel: str,
) -> str:
    if scalar == 0:
        return "neutral"

    if signal_transform == "adoption_only":
        return "balanced"

    if signal_transform in {"identity", "higher_is_citadel", "lower_is_citrini"}:
        return "citadel" if scalar > 0 else "citrini"

    if signal_transform in {"higher_is_citrini", "lower_is_citadel"}:
        return "citrini" if scalar > 0 else "citadel"

    if expected_direction_citadel not in {"up", "down"}:
        return "neutral"
    return _metric_direction_from_expectation(scalar=scalar, expected_direction_citadel=expected_direction_citadel)


def _metric_direction_from_expectation(*, scalar: Decimal, expected_direction_citadel: str) -> str:
    if scalar > 0:
        return "citadel" if expected_direction_citadel == "up" else "citrini"
    return "citadel" if expected_direction_citadel == "down" else "citrini"


def _feature_scalar(value: object) -> Decimal:
    if value is None:
        return Decimal("0.000")
    if isinstance(value, str):
        if value == "improving":
            return Decimal("1.000")
        if value == "deteriorating":
            return Decimal("-1.000")
        if value in {"flat", ""}:
            return Decimal("0.000")
        try:
            return _quantize(Decimal(value))
        except Exception:
            return Decimal("0.000")
    if isinstance(value, (int, float, Decimal)):
        return _quantize(Decimal(str(value)))
    return Decimal("0.000")


def _feature_strength(feature_payload: dict[str, object], feature_key: str, scalar: Decimal) -> Decimal:
    signal_key = f"{feature_key}_signal"
    signal_value = feature_payload.get(signal_key)
    if signal_value is not None:
        return min(abs(_feature_scalar(signal_value)), Decimal("1.000"))
    return min(abs(scalar), Decimal("1.000"))


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
            if claim.review_status in OPEN_QUESTION_REVIEW_STATUSES:
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
