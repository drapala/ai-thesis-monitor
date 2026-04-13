"""Review endpoints for ai_thesis_monitor."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from ai_thesis_monitor.api.deps import SessionDep
from ai_thesis_monitor.db.models.analytics import Claim

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/claims")
def list_claims(session: SessionDep) -> dict[str, list[dict[str, object]]]:
    claims = session.scalars(
        select(Claim)
        .where(Claim.review_status == "pending_review")
        .order_by(Claim.created_at.desc(), Claim.id.desc())
    ).all()
    return {
        "items": [
            {
                "id": claim.id,
                "module_key": claim.module_key,
                "claim_type": claim.claim_type,
                "entity": claim.entity,
                "claim_text": claim.claim_text,
                "evidence_direction": claim.evidence_direction,
                "strength": float(claim.strength),
                "confidence": float(claim.confidence),
                "evidence_date": claim.evidence_date,
                "published_date": claim.published_date,
                "review_status": claim.review_status,
            }
            for claim in claims
        ]
    }


@router.post("/claims/{claim_id}")
def review_claim(claim_id: int, status: str, session: SessionDep) -> dict[str, str | int]:
    claim = session.get(Claim, claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    claim.review_status = status
    session.commit()
    return {"claim_id": claim_id, "status": claim.review_status}
