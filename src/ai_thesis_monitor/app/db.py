"""Database helpers for ai_thesis_monitor."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from ai_thesis_monitor.app.settings import Settings


def build_engine(settings: Settings) -> Engine:
    return create_engine(settings.database_url, future=True)


def build_session_factory(settings: Settings) -> sessionmaker:
    engine = build_engine(settings)
    return sessionmaker(bind=engine, future=True, expire_on_commit=False)
