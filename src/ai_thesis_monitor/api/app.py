"""FastAPI application factory for ai_thesis_monitor."""

from __future__ import annotations

import os

from fastapi import FastAPI

from ai_thesis_monitor.api.routes.health import router as health_router
from ai_thesis_monitor.app.logging import configure_logging
from ai_thesis_monitor.app.settings import Settings


def create_app() -> FastAPI:
    configure_logging()
    settings = Settings.from_env(os.environ)
    app = FastAPI(title=settings.app_name)
    app.state.settings = settings
    app.include_router(health_router)
    return app
