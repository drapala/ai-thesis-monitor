from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from ai_thesis_monitor.domain.scoring.evidence import EvidenceRecord

TEXTUAL_CAP = Decimal("0.35")


@dataclass(frozen=True)
class ModuleScoreResult:
    module_key: str
    score_citadel: Decimal
    score_citrini: Decimal
    confidence: Decimal
    regime: str


def aggregate_module_score(module_key: str, evidence: list[EvidenceRecord]) -> ModuleScoreResult:
    citadel = Decimal("0")
    citrini = Decimal("0")
    textual_citrini = Decimal("0")

    for row in evidence:
        if row.evidence_type == "claim":
            textual_citrini += row.contribution_citrini
        citadel += row.contribution_citadel
        citrini += row.contribution_citrini

    max_textual = (citadel + citrini) * TEXTUAL_CAP if (citadel + citrini) else Decimal("0")
    if textual_citrini > max_textual:
        citrini -= textual_citrini - max_textual

    net = citadel - citrini
    regime = "neutral"
    if net <= Decimal("-0.50"):
        regime = "strong_citrini"
    elif net < Decimal("0"):
        regime = "leaning_citrini"
    elif net >= Decimal("0.50"):
        regime = "strong_citadel"
    elif net > Decimal("0"):
        regime = "leaning_citadel"

    confidence = min(Decimal("0.95"), Decimal("0.50") + (abs(net) / Decimal("4")))
    return ModuleScoreResult(
        module_key=module_key,
        score_citadel=citadel.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP),
        score_citrini=citrini.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP),
        confidence=confidence.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP),
        regime=regime,
    )
