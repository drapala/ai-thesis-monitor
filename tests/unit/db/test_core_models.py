"""Unit tests for core SQLAlchemy model registration."""

from sqlalchemy import UniqueConstraint

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


def test_core_table_columns_match_v1_contract() -> None:
    expected_columns_by_table = {
        "sources": {
            "id",
            "source_key",
            "source_name",
            "source_type",
            "base_url",
            "config",
            "reliability_score",
            "active",
            "created_at",
        },
        "metric_definitions": {
            "id",
            "metric_key",
            "module_key",
            "name",
            "description",
            "frequency",
            "unit",
            "lag_category",
            "weight",
            "expected_direction_citadel",
            "expected_direction_citrini",
            "primary_feature_key",
            "signal_transform",
            "min_history_points",
            "is_leading",
            "config",
            "is_active",
            "created_at",
        },
        "pipeline_runs": {
            "id",
            "run_type",
            "status",
            "triggered_by",
            "started_at",
            "finished_at",
            "inputs",
            "outputs_summary",
            "error_summary",
        },
        "job_runs": {
            "id",
            "pipeline_run_id",
            "job_name",
            "status",
            "started_at",
            "finished_at",
            "cursor_in",
            "cursor_out",
            "inputs",
            "outputs_summary",
            "error_summary",
        },
        "raw_observations": {
            "id",
            "source_id",
            "external_id",
            "payload",
            "content_hash",
            "observed_at",
            "published_at",
            "fetched_at",
        },
        "documents": {
            "id",
            "source_id",
            "raw_observation_id",
            "title",
            "url",
            "body_text",
            "published_at",
        },
        "document_chunks": {
            "id",
            "document_id",
            "chunk_index",
            "chunk_text",
            "chunk_hash",
        },
    }

    for table_name, expected_columns in expected_columns_by_table.items():
        table = Base.metadata.tables[table_name]
        assert expected_columns == set(table.columns.keys())


def test_core_uniqueness_constraints_match_contract() -> None:
    raw_observations = Base.metadata.tables["raw_observations"]
    document_chunks = Base.metadata.tables["document_chunks"]

    raw_observation_unique_columns = {
        tuple(constraint.columns.keys())
        for constraint in raw_observations.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    document_chunk_unique_columns = {
        tuple(constraint.columns.keys())
        for constraint in document_chunks.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert ("source_id", "content_hash") in raw_observation_unique_columns
    assert ("document_id", "chunk_index") in document_chunk_unique_columns
