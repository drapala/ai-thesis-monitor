"""Score endpoints for ai_thesis_monitor."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import func, select

from ai_thesis_monitor.api.deps import SessionDep
from ai_thesis_monitor.db.models.analytics import ModuleScore

router = APIRouter(prefix="/scores", tags=["scores"])


@router.get("/latest")
def read_latest_scores(session: SessionDep) -> dict[str, list[dict[str, object]]]:
    latest_score_date = session.scalar(select(func.max(ModuleScore.score_date)))
    if latest_score_date is None:
        return {"items": []}

    scores = session.scalars(
        select(ModuleScore)
        .where(ModuleScore.score_date == latest_score_date)
        .order_by(ModuleScore.module_key.asc(), ModuleScore.id.asc())
    ).all()
    return {
        "items": [
            {
                "module_key": score.module_key,
                "score_date": score.score_date,
                "score_citadel": float(score.score_citadel),
                "score_citrini": float(score.score_citrini),
                "confidence": float(score.confidence),
                "winning_thesis": score.winning_thesis,
                "regime": score.regime,
                "explanation": score.explanation,
            }
            for score in scores
        ]
    }
