"""Unit tests for the app settings module."""

from __future__ import annotations

from ai_thesis_monitor.app.settings import Settings


def test_settings_defaults_database_url() -> None:
    settings = Settings.from_env({})

    assert settings.database_url == (
        "postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor"
    )
