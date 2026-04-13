"""Narrative endpoints for ai_thesis_monitor."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/narratives", tags=["narratives"])


@router.get("/latest")
def read_latest_narrative() -> dict[str, None]:
    return {"snapshot": None}
