"""FastAPI application factory for ai_thesis_monitor."""

from __future__ import annotations

import os

from fastapi import FastAPI

from ai_thesis_monitor.api.routes.admin import router as admin_router
from ai_thesis_monitor.api.routes.alerts import router as alerts_router
from ai_thesis_monitor.api.routes.health import router as health_router
from ai_thesis_monitor.api.routes.narratives import router as narratives_router
from ai_thesis_monitor.api.routes.reviews import router as reviews_router
from ai_thesis_monitor.api.routes.scores import router as scores_router
from ai_thesis_monitor.app.db import build_session_factory
from ai_thesis_monitor.app.logging import configure_logging
from ai_thesis_monitor.app.settings import Settings


def create_app() -> FastAPI:
    configure_logging()
    settings = Settings.from_env(os.environ)
    app = FastAPI(title=settings.app_name)
    app.state.settings = settings
    app.state.session_factory = build_session_factory(settings)
    app.include_router(health_router)
    app.include_router(scores_router)
    app.include_router(alerts_router)
    app.include_router(narratives_router)
    app.include_router(reviews_router)
    app.include_router(admin_router)
    return app
