"""Replay utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_thesis_monitor.db.models.core import PipelineRun
from ai_thesis_monitor.ingestion.pipelines.weekly import run_weekly_pipeline


@dataclass(frozen=True)
class ReplayResult:
    module_scores_written: int
    tripwires_written: int
    alerts_written: int
    narratives_written: int


def replay_week(session: Session, *, start_date: str, end_date: str) -> ReplayResult:
    start_expr = PipelineRun.inputs.op("->>")("start_date")
    end_expr = PipelineRun.inputs.op("->>")("end_date")
    completed = session.scalar(
        select(PipelineRun).where(
            PipelineRun.run_type == "replay_week",
            PipelineRun.status == "completed",
            start_expr == start_date,
            end_expr == end_date,
        )
    )
    if completed is not None:
        return ReplayResult(0, 0, 0, 0)

    run = PipelineRun(
        run_type="replay_week",
        status="running",
        triggered_by="cli",
        inputs={"start_date": start_date, "end_date": end_date},
        outputs_summary={},
        error_summary=None,
    )
    session.add(run)
    session.flush()

    try:
        weekly_result = run_weekly_pipeline(
            module_histories={"labor": ["leaning_citrini", "strong_citrini"]},
            critical_claims={"labor": []},
        )
    except Exception:
        session.rollback()
        raise

    run.outputs_summary = {"mode": "replay"}
    run.status = "completed"
    run.finished_at = datetime.now(timezone.utc)
    session.commit()

    return ReplayResult(
        module_scores_written=weekly_result.module_scores_written,
        tripwires_written=weekly_result.tripwires_written,
        alerts_written=weekly_result.alerts_written,
        narratives_written=weekly_result.narratives_written,
    )
