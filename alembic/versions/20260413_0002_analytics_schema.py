"""Create analytics persistence schema."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260413_0002"
down_revision = "20260413_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "normalized_metrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("metric_definition_id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("raw_observation_id", sa.Integer(), nullable=True),
        sa.Column("geo", sa.String(length=255), nullable=True),
        sa.Column("segment", sa.String(length=255), nullable=True),
        sa.Column("observed_date", sa.Date(), nullable=False),
        sa.Column("value", sa.Numeric(), nullable=False),
        sa.Column("quality_score", sa.Numeric(precision=4, scale=3), nullable=False, server_default="0.800"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["metric_definition_id"], ["metric_definitions.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.ForeignKeyConstraint(["raw_observation_id"], ["raw_observations.id"]),
        sa.UniqueConstraint(
            "metric_definition_id",
            "source_id",
            "observed_date",
            "geo",
            "segment",
            name="uq_normalized_metric_semantic_key",
        ),
    )

    op.create_table(
        "metric_features",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("normalized_metric_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("feature_key", sa.String(length=255), nullable=False),
        sa.Column("feature_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["normalized_metric_id"], ["normalized_metrics.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "claims",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("raw_observation_id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("chunk_id", sa.Integer(), nullable=False),
        sa.Column("module_key", sa.String(length=255), nullable=False),
        sa.Column("claim_type", sa.String(length=255), nullable=False),
        sa.Column("entity", sa.String(length=255), nullable=True),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("evidence_direction", sa.String(length=64), nullable=False),
        sa.Column("strength", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("evidence_date", sa.Date(), nullable=True),
        sa.Column("published_date", sa.Date(), nullable=True),
        sa.Column("dedupe_key", sa.String(length=255), nullable=False, unique=True),
        sa.Column("review_status", sa.String(length=64), nullable=False, server_default="not_required"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.ForeignKeyConstraint(["raw_observation_id"], ["raw_observations.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.ForeignKeyConstraint(["chunk_id"], ["document_chunks.id"]),
    )

    op.create_table(
        "score_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("module_key", sa.String(length=255), nullable=False),
        sa.Column("score_date", sa.Date(), nullable=False),
        sa.Column("evidence_type", sa.String(length=64), nullable=False),
        sa.Column("bucket_key", sa.String(length=255), nullable=False),
        sa.Column("direction", sa.String(length=32), nullable=False),
        sa.Column("strength", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("impact", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("weight", sa.Numeric(precision=6, scale=3), nullable=False),
        sa.Column("quality", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("contribution_citadel", sa.Numeric(precision=8, scale=3), nullable=False),
        sa.Column("contribution_citrini", sa.Numeric(precision=8, scale=3), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("references", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "module_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("module_key", sa.String(length=255), nullable=False),
        sa.Column("score_date", sa.Date(), nullable=False),
        sa.Column("score_citadel", sa.Numeric(precision=8, scale=3), nullable=False),
        sa.Column("score_citrini", sa.Numeric(precision=8, scale=3), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("winning_thesis", sa.String(length=64), nullable=False),
        sa.Column("regime", sa.String(length=64), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("module_key", "score_date", name="uq_module_scores"),
    )

    op.create_table(
        "tripwire_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("module_key", sa.String(length=255), nullable=False),
        sa.Column("tripwire_key", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("direction", sa.String(length=32), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("trigger_type", sa.String(length=64), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("decay_factor", sa.Numeric(precision=4, scale=3), nullable=False, server_default="1.000"),
        sa.Column("evidence_refs", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("review_status", sa.String(length=64), nullable=False, server_default="not_required"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("alert_key", sa.String(length=255), nullable=False),
        sa.Column("module_key", sa.String(length=255), nullable=True),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
    )

    op.create_table(
        "narrative_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("snapshot_date", sa.Date(), nullable=False, unique=True),
        sa.Column("overall_winner", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=4, scale=3), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("module_breakdown", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("supporting_evidence", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("narrative_snapshots")
    op.drop_table("alerts")
    op.drop_table("tripwire_events")
    op.drop_table("module_scores")
    op.drop_table("score_evidence")
    op.drop_table("claims")
    op.drop_table("metric_features")
    op.drop_table("normalized_metrics")
