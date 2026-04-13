"""Review endpoints for ai_thesis_monitor."""

from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter

router = APIRouter(prefix="/reviews")


class ClaimStatusUpdate(BaseModel):
    status: str


@router.get("/claims")
def list_claims() -> dict[str, list]:
    return {"items": []}


@router.post("/claims/{claim_id}")
def update_claim(claim_id: str, update: ClaimStatusUpdate) -> dict[str, str]:
    return {"claim_id": claim_id, "status": update.status}
