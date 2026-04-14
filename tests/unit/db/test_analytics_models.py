"""Unit tests for analytics SQLAlchemy model registration."""

from sqlalchemy import UniqueConstraint

from ai_thesis_monitor.db.models.base import Base
from ai_thesis_monitor.db.models import analytics  # noqa: F401


def test_analytics_table_names_are_registered() -> None:
    expected_tables = {
        "normalized_metrics",
        "metric_features",
        "claims",
        "score_evidence",
        "module_scores",
        "tripwire_events",
        "alerts",
        "narrative_snapshots",
    }

    assert expected_tables.issubset(set(Base.metadata.tables))


def test_analytics_table_columns_match_v1_contract() -> None:
    expected_columns_by_table = {
        "score_evidence": {
            "id",
            "module_key",
            "score_date",
            "evidence_type",
            "bucket_key",
            "direction",
            "strength",
            "impact",
            "weight",
            "quality",
            "contribution_citadel",
            "contribution_citrini",
            "explanation",
            "references",
            "created_at",
        },
        "tripwire_events": {
            "id",
            "module_key",
            "tripwire_key",
            "title",
            "description",
            "direction",
            "severity",
            "trigger_type",
            "event_date",
            "valid_until",
            "decay_factor",
            "evidence_refs",
            "review_status",
            "created_at",
        },
        "claims": {
            "id",
            "source_id",
            "raw_observation_id",
            "document_id",
            "chunk_id",
            "module_key",
            "claim_type",
            "entity",
            "claim_text",
            "evidence_direction",
            "strength",
            "confidence",
            "evidence_date",
            "published_date",
            "dedupe_key",
            "review_status",
            "created_at",
        },
    }

    for table_name, expected_columns in expected_columns_by_table.items():
        table = Base.metadata.tables[table_name]
        assert expected_columns == set(table.columns.keys())


def test_analytics_uniqueness_constraints_match_contract() -> None:
    normalized_metrics = Base.metadata.tables["normalized_metrics"]
    claims = Base.metadata.tables["claims"]
    module_scores = Base.metadata.tables["module_scores"]
    narrative_snapshots = Base.metadata.tables["narrative_snapshots"]

    normalized_metrics_unique_columns = {
        tuple(constraint.columns.keys())
        for constraint in normalized_metrics.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    claims_unique_columns = {
        tuple(constraint.columns.keys())
        for constraint in claims.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    module_scores_unique_columns = {
        tuple(constraint.columns.keys())
        for constraint in module_scores.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    narrative_snapshots_unique_columns = {
        tuple(constraint.columns.keys())
        for constraint in narrative_snapshots.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    semantic_key = (
        "metric_definition_id",
        "source_id",
        "observed_date",
        "geo",
        "segment",
    )
    assert semantic_key in normalized_metrics_unique_columns
    assert ("dedupe_key",) in claims_unique_columns
    assert ("module_key", "score_date") in module_scores_unique_columns
    assert ("snapshot_date",) in narrative_snapshots_unique_columns

    semantic_constraint = next(
        constraint
        for constraint in normalized_metrics.constraints
        if isinstance(constraint, UniqueConstraint) and tuple(constraint.columns.keys()) == semantic_key
    )
    assert semantic_constraint.dialect_options["postgresql"].get("nulls_not_distinct") is True
