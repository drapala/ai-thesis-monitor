"""Admin endpoints for ai_thesis_monitor."""

from __future__ import annotations

from fastapi import APIRouter

from ai_thesis_monitor.api.deps import SessionDep
from ai_thesis_monitor.db.models.core import PipelineRun

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/jobs/{job_name}")
def trigger_job(job_name: str, session: SessionDep) -> dict[str, str]:
    session.add(
        PipelineRun(
            run_type=job_name,
            status="accepted",
            triggered_by="api",
            inputs={"job_name": job_name},
            outputs_summary={},
        )
    )
    session.commit()
    return {"job_name": job_name, "status": "accepted"}
