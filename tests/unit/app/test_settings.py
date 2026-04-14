"""Unit tests for the app settings module."""

from __future__ import annotations

import pytest

from ai_thesis_monitor.app.settings import (
    DEFAULT_DATABASE_URL,
    DEFAULT_FRED_BASE_URL,
    DEFAULT_RSS_REQUEST_TIMEOUT_SECONDS,
    Settings,
)


def test_settings_defaults_from_env() -> None:
    settings = Settings.from_env({})

    assert settings.database_url == DEFAULT_DATABASE_URL
    assert settings.fred_base_url == DEFAULT_FRED_BASE_URL
    assert settings.rss_request_timeout_seconds == DEFAULT_RSS_REQUEST_TIMEOUT_SECONDS


def test_settings_respects_overrides() -> None:
    overrides = {
        "APP_NAME": "overridden",
        "DATABASE_URL": "postgresql+psycopg://custom/db",
        "FRED_BASE_URL": "https://fred.example.org",
        "RSS_REQUEST_TIMEOUT_SECONDS": "5.5",
    }

    settings = Settings.from_env(overrides)

    assert settings.app_name == "overridden"
    assert settings.database_url == "postgresql+psycopg://custom/db"
    assert settings.fred_base_url == "https://fred.example.org"
    assert settings.rss_request_timeout_seconds == 5.5


@pytest.mark.parametrize("raw", ["not-a-number", "0", "-5"])
def test_settings_invalid_timeout_falls_back(raw: str) -> None:
    settings = Settings.from_env({"RSS_REQUEST_TIMEOUT_SECONDS": raw})

    assert settings.rss_request_timeout_seconds == DEFAULT_RSS_REQUEST_TIMEOUT_SECONDS
