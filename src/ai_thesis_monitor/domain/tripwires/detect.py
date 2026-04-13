"""Tripwire detection routines."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class TripwireResult:
    tripwire_key: str
    module_key: str
    severity: str
    direction: str
    trigger_type: str
    event_date: date
    valid_until: date
    decay_factor: float


def detect_tripwires(
    *,
    module_key: str,
    score_dates: list[date],
    regimes: list[str],
    critical_claims: list[str],
) -> list[TripwireResult]:
    tripwires: list[TripwireResult] = []
    if len(regimes) >= 3 and regimes[-3:] == ["leaning_citrini", "leaning_citrini", "strong_citrini"]:
        tripwires.append(
            TripwireResult(
                tripwire_key=f"{module_key}_persistent_deterioration_3w",
                module_key=module_key,
                severity="warning",
                direction="citrini",
                trigger_type="pattern",
                event_date=score_dates[-1],
                valid_until=score_dates[-1] + timedelta(days=21),
                decay_factor=0.900,
            )
        )
    if critical_claims:
        tripwires.append(
            TripwireResult(
                tripwire_key=f"{module_key}_critical_claim",
                module_key=module_key,
                severity="critical",
                direction="citrini",
                trigger_type="claim",
                event_date=score_dates[-1],
                valid_until=score_dates[-1] + timedelta(days=14),
                decay_factor=1.000,
            )
        )
    return tripwires
