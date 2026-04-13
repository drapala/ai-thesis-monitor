"""Unit tests for core SQLAlchemy model registration."""

from ai_thesis_monitor.db.models.base import Base
from ai_thesis_monitor.db.models import core  # noqa: F401


def test_core_table_names_are_registered() -> None:
    expected_tables = {
        "sources",
        "metric_definitions",
        "pipeline_runs",
        "job_runs",
        "raw_observations",
        "documents",
        "document_chunks",
    }

    assert expected_tables.issubset(set(Base.metadata.tables))
