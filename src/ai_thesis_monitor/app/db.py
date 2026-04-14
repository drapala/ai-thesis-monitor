"""Database helpers for ai_thesis_monitor."""

from __future__ import annotations

from typing import Dict

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from ai_thesis_monitor.app.settings import Settings


_ENGINE_CACHE: Dict[str, Engine] = {}


def build_engine(settings: Settings) -> Engine:
    cached = _ENGINE_CACHE.get(settings.database_url)
    if cached is not None:
        return cached
    engine = create_engine(settings.database_url, future=True)
    _ENGINE_CACHE[settings.database_url] = engine
    return engine


def build_session_factory(settings: Settings) -> sessionmaker:
    engine = build_engine(settings)
    return sessionmaker(bind=engine, future=True, expire_on_commit=False)
