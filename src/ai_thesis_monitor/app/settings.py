"""Settings management helpers for ai_thesis_monitor."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


DEFAULT_APP_NAME = "ai-thesis-monitor"
DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor"
)
DEFAULT_FRED_BASE_URL = "https://fred.stlouisfed.org"
DEFAULT_RSS_REQUEST_TIMEOUT_SECONDS = 10.0


@dataclass(frozen=True)
class Settings:
    app_name: str
    database_url: str
    fred_base_url: str
    rss_request_timeout_seconds: float

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        source = env if env is not None else os.environ
        return cls(
            app_name=source.get("APP_NAME", DEFAULT_APP_NAME),
            database_url=source.get("DATABASE_URL", DEFAULT_DATABASE_URL),
            fred_base_url=source.get("FRED_BASE_URL", DEFAULT_FRED_BASE_URL),
            rss_request_timeout_seconds=cls._parse_timeout(source),
        )

    @staticmethod
    def _parse_timeout(env: Mapping[str, str]) -> float:
        raw = env.get("RSS_REQUEST_TIMEOUT_SECONDS")
        if raw is None:
            return DEFAULT_RSS_REQUEST_TIMEOUT_SECONDS
        try:
            value = float(raw)
        except ValueError:
            return DEFAULT_RSS_REQUEST_TIMEOUT_SECONDS
        if value <= 0:
            return DEFAULT_RSS_REQUEST_TIMEOUT_SECONDS
        return value
