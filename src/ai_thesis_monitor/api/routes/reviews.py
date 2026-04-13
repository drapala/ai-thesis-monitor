"""Review endpoints for ai_thesis_monitor."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/reviews")


@router.get("/claims")
def list_claims() -> dict[str, list]:
    return {"items": []}


@router.post("/claims/{claim_id}")
def review_claim(claim_id: int, status: str) -> dict[str, str]:
    return {"claim_id": claim_id, "status": status}
