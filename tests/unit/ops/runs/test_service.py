from __future__ import annotations

import pytest
from sqlalchemy import delete, select

from ai_thesis_monitor.db.models.core import JobRun, PipelineRun
from ai_thesis_monitor.ops.runs.service import start_job_run, start_pipeline_run


@pytest.fixture(autouse=True)
def clean_run_tables(db_session) -> None:
    db_session.execute(delete(JobRun))
    db_session.execute(delete(PipelineRun))
    db_session.commit()
    yield
    db_session.execute(delete(JobRun))
    db_session.execute(delete(PipelineRun))
    db_session.commit()


def test_start_pipeline_run_inserts_running_row_with_flushed_id(db_session) -> None:
    inputs = {"mode": "full", "attempt": 1}

    run = start_pipeline_run(
        db_session,
        run_type="daily_refresh",
        triggered_by="tests",
        inputs=inputs,
    )

    assert run.id is not None
    assert run.status == "running"
    assert run.started_at is not None
    assert run.inputs == inputs
    assert run.triggered_by == "tests"
    assert run.run_type == "daily_refresh"

    stored = db_session.scalar(select(PipelineRun).where(PipelineRun.id == run.id))
    assert stored is not None
    assert stored.id == run.id
    assert stored.status == "running"
    assert stored.started_at is not None
    assert stored.inputs == inputs


def test_start_job_run_inserts_running_row_with_pipeline_link(db_session) -> None:
    pipeline_run = start_pipeline_run(
        db_session,
        run_type="weekly_refresh",
        triggered_by="tests",
        inputs={"scope": "unit"},
    )
    job_inputs = {"window": "7d"}

    job_run = start_job_run(
        db_session,
        pipeline_run_id=pipeline_run.id,
        job_name="normalize_metrics",
        inputs=job_inputs,
    )

    assert job_run.id is not None
    assert job_run.status == "running"
    assert job_run.started_at is not None
    assert job_run.inputs == job_inputs
    assert job_run.pipeline_run_id == pipeline_run.id
    assert job_run.job_name == "normalize_metrics"

    stored = db_session.scalar(select(JobRun).where(JobRun.id == job_run.id))
    assert stored is not None
    assert stored.id == job_run.id
    assert stored.pipeline_run_id == pipeline_run.id
    assert stored.status == "running"
    assert stored.started_at is not None
    assert stored.inputs == job_inputs

