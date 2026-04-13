"""Score endpoints for ai_thesis_monitor."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/scores", tags=["scores"])


@router.get("/latest")
def read_latest_scores() -> dict[str, list]:
    return {"items": []}
