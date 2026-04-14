"""Narrative endpoints for ai_thesis_monitor."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from ai_thesis_monitor.api.deps import SessionDep
from ai_thesis_monitor.db.models.analytics import NarrativeSnapshot

router = APIRouter(prefix="/narratives", tags=["narratives"])


@router.get("/latest")
def read_latest_narrative(session: SessionDep) -> dict[str, dict[str, object] | None]:
    snapshot = session.scalar(
        select(NarrativeSnapshot).order_by(NarrativeSnapshot.snapshot_date.desc(), NarrativeSnapshot.id.desc())
    )
    if snapshot is None:
        return {"snapshot": None}
    return {
        "snapshot": {
            "snapshot_date": snapshot.snapshot_date,
            "overall_winner": snapshot.overall_winner,
            "confidence": float(snapshot.confidence),
            "summary": snapshot.summary,
            "module_breakdown": snapshot.module_breakdown,
            "supporting_evidence": snapshot.supporting_evidence,
        }
    }
