"""Alert endpoints for ai_thesis_monitor."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from ai_thesis_monitor.api.deps import SessionDep
from ai_thesis_monitor.db.models.analytics import Alert

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
def list_alerts(session: SessionDep) -> dict[str, list[dict[str, object]]]:
    alerts = session.scalars(select(Alert).order_by(Alert.triggered_at.desc(), Alert.id.desc())).all()
    return {
        "items": [
            {
                "id": alert.id,
                "alert_key": alert.alert_key,
                "module_key": alert.module_key,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "triggered_at": alert.triggered_at,
                "acknowledged_at": alert.acknowledged_at,
                "status": alert.status,
            }
            for alert in alerts
        ]
    }
