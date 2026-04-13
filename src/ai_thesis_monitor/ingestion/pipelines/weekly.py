"""Weekly score ingestion glue."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from ai_thesis_monitor.domain.narratives.build import build_weekly_summary
from ai_thesis_monitor.domain.tripwires.detect import detect_tripwires


@dataclass(frozen=True)
class WeeklyPipelineResult:
    module_scores_written: int
    tripwires_written: int
    alerts_written: int
    narratives_written: int


def run_weekly_pipeline(
    *,
    module_histories: dict[str, list[str]],
    critical_claims: dict[str, list[str]],
) -> WeeklyPipelineResult:
    tripwire_total = 0
    for module_key, regimes in module_histories.items():
        score_dates = [
            date(2026, 4, 13) - timedelta(days=7 * offset)
            for offset in range(len(regimes) - 1, -1, -1)
        ]
        tripwire_total += len(
            detect_tripwires(
                module_key=module_key,
                score_dates=score_dates,
                regimes=regimes,
                critical_claims=critical_claims.get(module_key, []),
            )
        )
    _ = build_weekly_summary(
        overall_winner="neutral",
        module_regimes={key: values[-1] for key, values in module_histories.items() if values},
        new_evidence=[],
        open_questions=[],
    )
    return WeeklyPipelineResult(
        module_scores_written=sum(len(values) for values in module_histories.values()),
        tripwires_written=tripwire_total,
        alerts_written=tripwire_total,
        narratives_written=1,
    )
