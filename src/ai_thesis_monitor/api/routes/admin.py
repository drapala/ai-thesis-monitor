"""Admin endpoints for ai_thesis_monitor."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/jobs/{job_name}")
def trigger_job(job_name: str) -> dict[str, str]:
    return {"job_name": job_name, "status": "accepted"}
