"""Settings management helpers for ai_thesis_monitor."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


DEFAULT_APP_NAME = "ai-thesis-monitor"
DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor"
)
DEFAULT_FRED_BASE_URL = "https://api.stlouisfed.org"
DEFAULT_RSS_REQUEST_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class Settings:
    app_name: str
    database_url: str
    fred_base_url: str
    rss_request_timeout_seconds: int

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "Settings":
        return cls(
            app_name=env.get("APP_NAME", DEFAULT_APP_NAME),
            database_url=env.get("DATABASE_URL", DEFAULT_DATABASE_URL),
            fred_base_url=env.get("FRED_BASE_URL", DEFAULT_FRED_BASE_URL),
            rss_request_timeout_seconds=cls._parse_timeout(env),
        )

    @staticmethod
    def _parse_timeout(env: Mapping[str, str]) -> int:
        raw = env.get("RSS_REQUEST_TIMEOUT_SECONDS")
        if raw is None:
            return DEFAULT_RSS_REQUEST_TIMEOUT_SECONDS
        try:
            return int(raw)
        except ValueError:
            return DEFAULT_RSS_REQUEST_TIMEOUT_SECONDS
