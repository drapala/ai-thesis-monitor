from dataclasses import dataclass
from decimal import Decimal
from typing import Dict


@dataclass(frozen=True)
class EvidenceRecord:
    module_key: str
    evidence_type: str
    bucket_key: str
    direction: str
    strength: Decimal
    impact: Decimal
    weight: Decimal
    quality: Decimal
    contribution_citadel: Decimal
    contribution_citrini: Decimal
    explanation: str
    references: Dict[str, str]
