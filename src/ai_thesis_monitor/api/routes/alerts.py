"""Alert endpoints for ai_thesis_monitor."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
def list_alerts() -> dict[str, list]:
    return {"items": []}
