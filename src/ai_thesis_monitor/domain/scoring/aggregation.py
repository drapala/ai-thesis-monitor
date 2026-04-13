from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from ai_thesis_monitor.domain.scoring.evidence import EvidenceRecord

TEXTUAL_CAP = Decimal("0.35")
ONE_MINUS_CAP = Decimal("1") - TEXTUAL_CAP


@dataclass(frozen=True)
class ModuleScoreResult:
    module_key: str
    score_citadel: Decimal
    score_citrini: Decimal
    confidence: Decimal
    regime: str


def _cap_textual_share(textual: Decimal, non_textual: Decimal) -> Decimal:
    if not textual:
        return textual
    if non_textual <= 0:
        return Decimal("0")
    max_textual = (TEXTUAL_CAP * non_textual) / ONE_MINUS_CAP
    return min(textual, max_textual)


def aggregate_module_score(module_key: str, evidence: list[EvidenceRecord]) -> ModuleScoreResult:
    non_textual_citadel = Decimal("0")
    non_textual_citrini = Decimal("0")
    textual_citadel = Decimal("0")
    textual_citrini = Decimal("0")

    for row in evidence:
        if row.evidence_type == "claim":
            textual_citadel += row.contribution_citadel
            textual_citrini += row.contribution_citrini
        else:
            non_textual_citadel += row.contribution_citadel
            non_textual_citrini += row.contribution_citrini

    total_non_textual = non_textual_citadel + non_textual_citrini
    textual_total = textual_citadel + textual_citrini

    capped_textual_total = _cap_textual_share(textual_total, total_non_textual)
    if textual_total and capped_textual_total < textual_total:
        scale = capped_textual_total / textual_total
        textual_citadel = textual_citadel * scale
        textual_citrini = textual_citrini * scale
    if total_non_textual <= 0 and textual_total:
        textual_citadel = Decimal("0")
        textual_citrini = Decimal("0")

    citadel = non_textual_citadel + textual_citadel
    citrini = non_textual_citrini + textual_citrini

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
