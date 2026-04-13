"""Replay utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from hashlib import sha256
from typing import cast

import struct
from sqlalchemy.engine import Connection, Engine
from sqlalchemy import select, text
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
    _validate_date_window(start_date, end_date)
    with Session(bind=_replay_bind(session)) as replay_session:
        with replay_session.begin():
            return _replay_week_transaction(
                replay_session,
                start_date=start_date,
                end_date=end_date,
            )


def _compute_replay_lock_id(run_type: str, start_date: str, end_date: str) -> int:
    digest = sha256(f"{run_type}|{start_date}|{end_date}".encode("utf-8")).digest()
    return cast(int, struct.unpack(">q", digest[:8])[0])


def _replay_bind(session: Session) -> Engine:
    bind = session.get_bind()
    if isinstance(bind, Connection):
        return bind.engine
    return bind


def _replay_week_transaction(
    session: Session,
    *,
    start_date: str,
    end_date: str,
) -> ReplayResult:
    lock_id = _compute_replay_lock_id("replay_week", start_date, end_date)
    start_expr = PipelineRun.inputs.op("->>")("start_date")
    end_expr = PipelineRun.inputs.op("->>")("end_date")

    _acquire_replay_lock(session, lock_id)

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

    weekly_result = run_weekly_pipeline(
        session=session,
        score_date=date.fromisoformat(end_date),
    )

    run.outputs_summary = {
        "mode": "replay",
        "score_date": end_date,
        "module_scores_written": weekly_result.module_scores_written,
        "tripwires_written": weekly_result.tripwires_written,
        "alerts_written": weekly_result.alerts_written,
        "narratives_written": weekly_result.narratives_written,
    }
    run.status = "completed"
    run.finished_at = datetime.now(timezone.utc)

    return ReplayResult(
        module_scores_written=weekly_result.module_scores_written,
        tripwires_written=weekly_result.tripwires_written,
        alerts_written=weekly_result.alerts_written,
        narratives_written=weekly_result.narratives_written,
    )


def _acquire_replay_lock(session: Session, lock_id: int) -> None:
    session.execute(text("SELECT pg_advisory_xact_lock(:lock_id)"), {"lock_id": lock_id})


def _validate_date_window(start_date: str, end_date: str) -> None:
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError as exc:
        raise ValueError(f"invalid date window: {exc}") from exc

    if end < start:
        raise ValueError("end_date must not be earlier than start_date")
