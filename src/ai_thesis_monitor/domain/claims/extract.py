"""Rule-based claim extraction for text ingestion."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ExtractedClaim:
    module_key: str
    claim_type: str
    claim_text: str
    entity: str | None
    evidence_direction: str
    strength: Decimal
    confidence: Decimal
    review_status: str


_AI_WORD_RE = re.compile(r"\b(?:ai|a\.i\.|artificial intelligence)\b")
_LABOR_CUT_RE = re.compile(
    r"\b(?:layoff|layoffs|laying off|job cuts|cut jobs|cuts? .*work force|cuts? .*workforce|reduce workforce)\b"
)


def extract_claims(*, title: str, text: str) -> list[ExtractedClaim]:
    normalized = f"{title} {text}".lower()

    if _AI_WORD_RE.search(normalized) and _LABOR_CUT_RE.search(normalized):
        return [
            ExtractedClaim(
                module_key="labor",
                claim_type="headcount_reduction_ai_efficiency",
                claim_text=title,
                entity="ServiceNow" if "servicenow" in normalized else None,
                evidence_direction="citrini",
                strength=Decimal("0.82"),
                confidence=Decimal("0.76"),
                review_status="pending_review",
            )
        ]

    if "discount" in normalized and ("renewal" in normalized or "pricing" in normalized):
        return [
            ExtractedClaim(
                module_key="intermediation",
                claim_type="saas_renewal_discount_pressure",
                claim_text=title,
                entity=None,
                evidence_direction="citrini",
                strength=Decimal("0.65"),
                confidence=Decimal("0.60"),
                review_status="pending_review",
            )
        ]

    return []
