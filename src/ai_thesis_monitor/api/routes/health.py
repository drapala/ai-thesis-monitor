"""Health endpoint for ai_thesis_monitor."""

from __future__ import annotations

import os

from fastapi import APIRouter

from ai_thesis_monitor.app.settings import Settings

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    settings = Settings.from_env(os.environ)
    return {"status": "ok", "service": settings.app_name}
