from datetime import date

from ai_thesis_monitor.domain.tripwires.detect import detect_tripwires


def test_detect_tripwires_emits_pattern_tripwire_for_persistent_labor_deterioration() -> None:
    tripwires = detect_tripwires(
        module_key="labor",
        score_dates=[date(2026, 3, 23), date(2026, 3, 30), date(2026, 4, 6)],
        regimes=["leaning_citrini", "leaning_citrini", "strong_citrini"],
        critical_claims=[],
    )
    assert tripwires[0].tripwire_key == "labor_persistent_deterioration_3w"
