from decimal import Decimal

from ai_thesis_monitor.domain.scoring.aggregation import aggregate_module_score
from ai_thesis_monitor.domain.scoring.evidence import EvidenceRecord


def test_aggregate_module_score_caps_textual_contribution() -> None:
    evidence = [
        EvidenceRecord(module_key="labor", evidence_type="metric", bucket_key="labor_platforms", direction="citrini", strength=Decimal("0.9"), impact=Decimal("0.8"), weight=Decimal("1.2"), quality=Decimal("0.9"), contribution_citadel=Decimal("0"), contribution_citrini=Decimal("0.864"), explanation="jobs down", references={}),
        EvidenceRecord(module_key="labor", evidence_type="claim", bucket_key="textual_claims", direction="citrini", strength=Decimal("1.0"), impact=Decimal("1.0"), weight=Decimal("1.0"), quality=Decimal("1.0"), contribution_citadel=Decimal("0"), contribution_citrini=Decimal("1.000"), explanation="ai layoff", references={}),
    ]
    score = aggregate_module_score("labor", evidence)
    assert score.score_citrini == Decimal("1.329")
    assert score.regime in {"leaning_citrini", "strong_citrini"}


def test_aggregate_module_score_claim_only_textual_is_dropped() -> None:
    evidence = [
        EvidenceRecord(module_key="labor", evidence_type="claim", bucket_key="textual_claims", direction="citrini", strength=Decimal("1.0"), impact=Decimal("1.0"), weight=Decimal("1.0"), quality=Decimal("1.0"), contribution_citadel=Decimal("0.4"), contribution_citrini=Decimal("1.2"), explanation="text only", references={}),
    ]
    score = aggregate_module_score("labor", evidence)
    assert score.score_citadel == Decimal("0.000")
    assert score.score_citrini == Decimal("0.000")
    assert score.regime == "neutral"
