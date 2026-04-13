"""Services for creating pipeline and job run records."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from ai_thesis_monitor.db.models.core import JobRun, PipelineRun


def start_pipeline_run(
    session: Session,
    run_type: str,
    triggered_by: str,
    inputs: dict[str, Any],
) -> PipelineRun:
    run = PipelineRun(
        run_type=run_type,
        status="running",
        triggered_by=triggered_by,
        started_at=datetime.now(timezone.utc),
        inputs=inputs,
        outputs_summary={},
        error_summary=None,
    )
    session.add(run)
    session.flush()
    return run


def start_job_run(
    session: Session,
    pipeline_run_id: int,
    job_name: str,
    inputs: dict[str, Any],
) -> JobRun:
    run = JobRun(
        pipeline_run_id=pipeline_run_id,
        job_name=job_name,
        status="running",
        started_at=datetime.now(timezone.utc),
        inputs=inputs,
        outputs_summary={},
        error_summary=None,
    )
    session.add(run)
    session.flush()
    return run

