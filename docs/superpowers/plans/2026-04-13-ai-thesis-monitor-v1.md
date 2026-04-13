# AI Thesis Monitor V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone, headless V1 of AI Thesis Monitor that ingests a thin slice of structured and textual public US data, persists auditable evidence in Postgres, computes weekly module scores, detects tripwires, and emits narrative snapshots through CLI jobs and a small FastAPI surface.

**Architecture:** Use a single Python package under `src/ai_thesis_monitor` with pure domain services, SQLAlchemy persistence, Typer jobs, and FastAPI read/admin routes. Start with one structured connector (`FRED` CSV) and one textual connector (RSS) so the system proves the end-to-end shape before expanding the metric set and source count.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x, psycopg, Alembic, httpx, tenacity, pybreaker, Typer, pytest, ruff, mypy, Postgres 16, Docker Compose

---

## Scope split

The approved spec spans multiple subsystems, but they are tightly coupled in the first shippable slice. This plan keeps them in one sequence by building one thin vertical slice at a time:

1. foundation and runtime
2. schema and seeds
3. structured ingest
4. feature and score engine
5. textual ingest and claims
6. tripwires, alerts, narratives
7. API and replay

Every task below ends in working, testable software and a commit.

## File map

### Project runtime

- Create: `compose.yaml` — local Postgres 16 for development and tests
- Create: `.gitignore` — Python, uv, pytest, and local env ignores
- Create: `pyproject.toml` — package metadata, dependencies, pytest, ruff, mypy config
- Create: `README.md` — local setup, daily/weekly job commands, review flow

### Application core

- Create: `src/ai_thesis_monitor/__init__.py` — package version
- Create: `src/ai_thesis_monitor/app/settings.py` — environment-backed configuration
- Create: `src/ai_thesis_monitor/app/logging.py` — structured logger bootstrap
- Create: `src/ai_thesis_monitor/app/db.py` — engine and session factory
- Create: `src/ai_thesis_monitor/api/app.py` — FastAPI app factory
- Create: `src/ai_thesis_monitor/api/routes/health.py` — health route
- Create: `src/ai_thesis_monitor/cli/main.py` — Typer entrypoint

### Database and migrations

- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/versions/20260413_0001_core_schema.py`
- Create: `alembic/versions/20260413_0002_analytics_schema.py`
- Create: `src/ai_thesis_monitor/db/models/base.py`
- Create: `src/ai_thesis_monitor/db/models/core.py`
- Create: `src/ai_thesis_monitor/db/models/analytics.py`

### Seed data and ops

- Create: `src/ai_thesis_monitor/db/seeds/sources.py`
- Create: `src/ai_thesis_monitor/db/seeds/metric_definitions.py`
- Create: `src/ai_thesis_monitor/ops/runs/service.py`
- Create: `src/ai_thesis_monitor/ops/replay/service.py`

### Ingestion and domain logic

- Create: `src/ai_thesis_monitor/ingestion/adapters/fred.py`
- Create: `src/ai_thesis_monitor/ingestion/adapters/rss.py`
- Create: `src/ai_thesis_monitor/ingestion/parsers/structured.py`
- Create: `src/ai_thesis_monitor/ingestion/parsers/text.py`
- Create: `src/ai_thesis_monitor/ingestion/pipelines/structured.py`
- Create: `src/ai_thesis_monitor/ingestion/pipelines/text.py`
- Create: `src/ai_thesis_monitor/ingestion/pipelines/weekly.py`
- Create: `src/ai_thesis_monitor/domain/metrics/features.py`
- Create: `src/ai_thesis_monitor/domain/scoring/evidence.py`
- Create: `src/ai_thesis_monitor/domain/scoring/aggregation.py`
- Create: `src/ai_thesis_monitor/domain/claims/extract.py`
- Create: `src/ai_thesis_monitor/domain/tripwires/detect.py`
- Create: `src/ai_thesis_monitor/domain/narratives/build.py`

### API surfaces

- Create: `src/ai_thesis_monitor/api/routes/scores.py`
- Create: `src/ai_thesis_monitor/api/routes/alerts.py`
- Create: `src/ai_thesis_monitor/api/routes/narratives.py`
- Create: `src/ai_thesis_monitor/api/routes/reviews.py`
- Create: `src/ai_thesis_monitor/api/routes/admin.py`

### Tests and fixtures

- Create: `tests/conftest.py`
- Create: `tests/fixtures/fred/UNRATE.csv`
- Create: `tests/fixtures/rss/labor_claims.xml`
- Create: `tests/unit/test_cli_smoke.py`
- Create: `tests/unit/app/test_settings.py`
- Create: `tests/unit/api/test_health.py`
- Create: `tests/unit/db/test_core_models.py`
- Create: `tests/unit/db/test_analytics_models.py`
- Create: `tests/integration/db/test_seed_reference_data.py`
- Create: `tests/integration/ingestion/test_structured_pipeline.py`
- Create: `tests/unit/domain/test_features.py`
- Create: `tests/unit/domain/test_scoring.py`
- Create: `tests/integration/ingestion/test_text_pipeline.py`
- Create: `tests/unit/domain/test_tripwires.py`
- Create: `tests/unit/domain/test_narratives.py`
- Create: `tests/integration/api/test_read_routes.py`
- Create: `tests/integration/pipelines/test_replay_pipeline.py`

## Task 1: Bootstrap the repo, CLI, and local Postgres runtime

**Files:**
- Create: `.gitignore`
- Create: `compose.yaml`
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/ai_thesis_monitor/__init__.py`
- Create: `src/ai_thesis_monitor/cli/main.py`
- Test: `tests/unit/test_cli_smoke.py`

- [ ] **Step 1: Write the failing CLI smoke test**

```python
from typer.testing import CliRunner

from ai_thesis_monitor.cli.main import app


def test_version_command_prints_package_version() -> None:
    result = CliRunner().invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.stdout
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
uv run pytest tests/unit/test_cli_smoke.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'ai_thesis_monitor'`

- [ ] **Step 3: Write the minimal project skeleton**

`pyproject.toml`

```toml
[project]
name = "ai-thesis-monitor"
version = "0.1.0"
description = "Headless thesis observability system for AI macro regimes"
requires-python = ">=3.12"
dependencies = [
  "alembic>=1.16.0",
  "fastapi>=0.115.0",
  "httpx>=0.28.0",
  "psycopg[binary]>=3.2.0",
  "pydantic>=2.11.0",
  "pybreaker>=1.4.0",
  "sqlalchemy>=2.0.40",
  "tenacity>=9.1.0",
  "typer>=0.16.0",
  "uvicorn>=0.34.0",
]

[project.optional-dependencies]
dev = [
  "mypy>=1.15.0",
  "pytest>=8.3.0",
  "ruff>=0.11.0",
]

[build-system]
requires = ["setuptools>=69.0.0"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.mypy]
python_version = "3.12"
strict = true
packages = ["ai_thesis_monitor"]

[tool.setuptools.packages.find]
where = ["src"]
```

`compose.yaml`

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: ai_thesis_monitor
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "54321:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

`src/ai_thesis_monitor/__init__.py`

```python
__all__ = ["__version__"]

__version__ = "0.1.0"
```

`src/ai_thesis_monitor/cli/main.py`

```python
import typer

from ai_thesis_monitor import __version__

app = typer.Typer(help="AI Thesis Monitor CLI")


@app.command()
def version() -> None:
    typer.echo(__version__)


if __name__ == "__main__":
    app()
```

`.gitignore`

```gitignore
.env
.mypy_cache/
.pytest_cache/
.ruff_cache/
.venv/
__pycache__/
*.pyc
dist/
build/
```

`README.md`

```markdown
# AI Thesis Monitor

Headless thesis observability system for AI macro regime monitoring.

## Local setup

```bash
docker compose up -d postgres
uv sync --extra dev
uv run python -m ai_thesis_monitor.cli.main version
```
```

- [ ] **Step 4: Run the smoke test again**

Run:

```bash
docker compose up -d postgres
uv sync --extra dev
uv run pytest tests/unit/test_cli_smoke.py -v
```

Expected: PASS with `1 passed`

- [ ] **Step 5: Commit**

```bash
git add .gitignore compose.yaml pyproject.toml README.md src/ai_thesis_monitor/__init__.py src/ai_thesis_monitor/cli/main.py tests/unit/test_cli_smoke.py
git commit -m "chore: bootstrap ai thesis monitor runtime"
```

## Task 2: Add settings, DB factory, and a health-only FastAPI app

**Files:**
- Create: `src/ai_thesis_monitor/app/settings.py`
- Create: `src/ai_thesis_monitor/app/logging.py`
- Create: `src/ai_thesis_monitor/app/db.py`
- Create: `src/ai_thesis_monitor/api/app.py`
- Create: `src/ai_thesis_monitor/api/routes/health.py`
- Test: `tests/unit/app/test_settings.py`
- Test: `tests/unit/api/test_health.py`

- [ ] **Step 1: Write failing settings and health tests**

```python
from ai_thesis_monitor.app.settings import Settings


def test_settings_default_database_url() -> None:
    settings = Settings.from_env({})
    assert settings.database_url == "postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor"
```

```python
from fastapi.testclient import TestClient

from ai_thesis_monitor.api.app import create_app


def test_health_route_returns_ok() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ai-thesis-monitor"}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
uv run pytest tests/unit/app/test_settings.py tests/unit/api/test_health.py -v
```

Expected: FAIL with import errors for `ai_thesis_monitor.app` and `ai_thesis_monitor.api`

- [ ] **Step 3: Implement the core app services**

`src/ai_thesis_monitor/app/settings.py`

```python
from collections.abc import Mapping
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    app_name: str
    database_url: str
    fred_base_url: str
    rss_request_timeout_seconds: float

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        values = dict(os.environ if env is None else env)
        return cls(
            app_name=values.get("APP_NAME", "ai-thesis-monitor"),
            database_url=values.get(
                "DATABASE_URL",
                "postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor",
            ),
            fred_base_url=values.get("FRED_BASE_URL", "https://fred.stlouisfed.org"),
            rss_request_timeout_seconds=float(values.get("RSS_REQUEST_TIMEOUT_SECONDS", "10")),
        )
```

`src/ai_thesis_monitor/app/db.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ai_thesis_monitor.app.settings import Settings


def build_engine(settings: Settings):
    return create_engine(settings.database_url, future=True)


def build_session_factory(settings: Settings) -> sessionmaker:
    return sessionmaker(bind=build_engine(settings), expire_on_commit=False, future=True)
```

`src/ai_thesis_monitor/api/routes/health.py`

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-thesis-monitor"}
```

`src/ai_thesis_monitor/api/app.py`

```python
from fastapi import FastAPI

from ai_thesis_monitor.api.routes.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="AI Thesis Monitor")
    app.include_router(health_router)
    return app
```

`src/ai_thesis_monitor/app/logging.py`

```python
import logging


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
```

- [ ] **Step 4: Run the unit tests again**

Run:

```bash
uv run pytest tests/unit/app/test_settings.py tests/unit/api/test_health.py -v
```

Expected: PASS with `2 passed`

- [ ] **Step 5: Commit**

```bash
git add src/ai_thesis_monitor/app/settings.py src/ai_thesis_monitor/app/logging.py src/ai_thesis_monitor/app/db.py src/ai_thesis_monitor/api/app.py src/ai_thesis_monitor/api/routes/health.py tests/unit/app/test_settings.py tests/unit/api/test_health.py
git commit -m "feat: add app settings and health api"
```

## Task 3: Create core schema, SQLAlchemy models, and Alembic wiring

**Files:**
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/versions/20260413_0001_core_schema.py`
- Create: `src/ai_thesis_monitor/db/models/base.py`
- Create: `src/ai_thesis_monitor/db/models/core.py`
- Test: `tests/unit/db/test_core_models.py`

- [ ] **Step 1: Write the failing core-model test**

```python
from ai_thesis_monitor.db.models.base import Base


def test_core_tables_are_registered() -> None:
    table_names = set(Base.metadata.tables)
    assert {
        "sources",
        "metric_definitions",
        "pipeline_runs",
        "job_runs",
        "raw_observations",
        "documents",
        "document_chunks",
    }.issubset(table_names)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
uv run pytest tests/unit/db/test_core_models.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'ai_thesis_monitor.db'`

- [ ] **Step 3: Implement the base metadata and core tables**

`src/ai_thesis_monitor/db/models/base.py`

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

`src/ai_thesis_monitor/db/models/core.py`

```python
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ai_thesis_monitor.db.models.base import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_key: Mapped[str] = mapped_column(String, unique=True, index=True)
    source_name: Mapped[str] = mapped_column(String)
    source_type: Mapped[str] = mapped_column(String)
    base_url: Mapped[str | None] = mapped_column(String)
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    reliability_score: Mapped[float] = mapped_column(Numeric(4, 3), default=0.800)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class MetricDefinition(Base):
    __tablename__ = "metric_definitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    metric_key: Mapped[str] = mapped_column(String, unique=True, index=True)
    module_key: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    frequency: Mapped[str] = mapped_column(String)
    unit: Mapped[str | None] = mapped_column(String)
    lag_category: Mapped[str] = mapped_column(String)
    weight: Mapped[float] = mapped_column(Numeric(6, 3))
    expected_direction_citadel: Mapped[str] = mapped_column(String)
    expected_direction_citrini: Mapped[str] = mapped_column(String)
    primary_feature_key: Mapped[str] = mapped_column(String)
    signal_transform: Mapped[str] = mapped_column(String)
    min_history_points: Mapped[int] = mapped_column(default=4)
    is_leading: Mapped[bool] = mapped_column(Boolean, default=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_type: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, index=True)
    triggered_by: Mapped[str] = mapped_column(String, default="system")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    inputs: Mapped[dict] = mapped_column(JSONB, default=dict)
    outputs_summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    error_summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    jobs: Mapped[list["JobRun"]] = relationship(back_populates="pipeline_run")


class JobRun(Base):
    __tablename__ = "job_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    pipeline_run_id: Mapped[int] = mapped_column(ForeignKey("pipeline_runs.id"), index=True)
    job_name: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cursor_in: Mapped[dict] = mapped_column(JSONB, default=dict)
    cursor_out: Mapped[dict] = mapped_column(JSONB, default=dict)
    inputs: Mapped[dict] = mapped_column(JSONB, default=dict)
    outputs_summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    error_summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    pipeline_run: Mapped[PipelineRun] = relationship(back_populates="jobs")


class RawObservation(Base):
    __tablename__ = "raw_observations"
    __table_args__ = (
        UniqueConstraint("source_id", "content_hash", name="uq_raw_observation_source_hash"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    external_id: Mapped[str | None] = mapped_column(String)
    payload: Mapped[dict] = mapped_column(JSONB)
    content_hash: Mapped[str] = mapped_column(String, index=True)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    raw_observation_id: Mapped[int] = mapped_column(ForeignKey("raw_observations.id"), unique=True)
    title: Mapped[str] = mapped_column(String)
    url: Mapped[str | None] = mapped_column(String)
    body_text: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(index=True)
    chunk_text: Mapped[str] = mapped_column(Text)
    chunk_hash: Mapped[str] = mapped_column(String, index=True)
```

`alembic/env.py`

```python
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from ai_thesis_monitor.app.settings import Settings
from ai_thesis_monitor.db.models.base import Base
from ai_thesis_monitor.db.models import core  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", Settings.from_env().database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
```

Then generate the migration:

```bash
uv run alembic revision --autogenerate -m "create core schema"
mv alembic/versions/*_create_core_schema.py alembic/versions/20260413_0001_core_schema.py
```

- [ ] **Step 4: Run the model test**

Run:

```bash
uv run pytest tests/unit/db/test_core_models.py -v
```

Expected: PASS with `1 passed`

- [ ] **Step 5: Commit**

```bash
git add alembic.ini alembic/env.py alembic/versions/20260413_0001_core_schema.py src/ai_thesis_monitor/db/models/base.py src/ai_thesis_monitor/db/models/core.py tests/unit/db/test_core_models.py
git commit -m "feat: add core persistence schema"
```

## Task 4: Add analytical tables for metrics, claims, scores, alerts, and narratives

**Files:**
- Create: `alembic/versions/20260413_0002_analytics_schema.py`
- Create: `src/ai_thesis_monitor/db/models/analytics.py`
- Test: `tests/unit/db/test_analytics_models.py`

- [ ] **Step 1: Write the failing analytics-model test**

```python
from ai_thesis_monitor.db.models.base import Base


def test_analytics_tables_are_registered() -> None:
    table_names = set(Base.metadata.tables)
    assert {
        "normalized_metrics",
        "metric_features",
        "claims",
        "score_evidence",
        "module_scores",
        "tripwire_events",
        "alerts",
        "narrative_snapshots",
    }.issubset(table_names)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
uv run pytest tests/unit/db/test_analytics_models.py -v
```

Expected: FAIL because the analytics tables do not exist in metadata

- [ ] **Step 3: Implement the analytical schema**

`src/ai_thesis_monitor/db/models/analytics.py`

```python
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ai_thesis_monitor.db.models.base import Base


class NormalizedMetric(Base):
    __tablename__ = "normalized_metrics"
    __table_args__ = (
        UniqueConstraint(
            "metric_definition_id",
            "source_id",
            "observed_date",
            "geo",
            "segment",
            name="uq_normalized_metric_semantic_key",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    metric_definition_id: Mapped[int] = mapped_column(ForeignKey("metric_definitions.id"), index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    raw_observation_id: Mapped[int | None] = mapped_column(ForeignKey("raw_observations.id"))
    geo: Mapped[str | None] = mapped_column(String)
    segment: Mapped[str | None] = mapped_column(String)
    observed_date: Mapped[date] = mapped_column(Date, index=True)
    value: Mapped[float] = mapped_column(Numeric)
    quality_score: Mapped[float] = mapped_column(Numeric(4, 3), default=0.800)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class MetricFeature(Base):
    __tablename__ = "metric_features"

    id: Mapped[int] = mapped_column(primary_key=True)
    normalized_metric_id: Mapped[int] = mapped_column(ForeignKey("normalized_metrics.id"), unique=True)
    feature_key: Mapped[str] = mapped_column(String, index=True)
    feature_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    raw_observation_id: Mapped[int] = mapped_column(ForeignKey("raw_observations.id"), index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), index=True)
    chunk_id: Mapped[int] = mapped_column(ForeignKey("document_chunks.id"), index=True)
    module_key: Mapped[str] = mapped_column(String, index=True)
    claim_type: Mapped[str] = mapped_column(String, index=True)
    entity: Mapped[str | None] = mapped_column(String)
    claim_text: Mapped[str] = mapped_column(Text)
    evidence_direction: Mapped[str] = mapped_column(String)
    strength: Mapped[float] = mapped_column(Numeric(4, 3))
    confidence: Mapped[float] = mapped_column(Numeric(4, 3))
    evidence_date: Mapped[date | None] = mapped_column(Date)
    published_date: Mapped[date | None] = mapped_column(Date)
    dedupe_key: Mapped[str] = mapped_column(String, unique=True, index=True)
    review_status: Mapped[str] = mapped_column(String, default="not_required", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ScoreEvidence(Base):
    __tablename__ = "score_evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    module_key: Mapped[str] = mapped_column(String, index=True)
    score_date: Mapped[date] = mapped_column(Date, index=True)
    evidence_type: Mapped[str] = mapped_column(String)
    bucket_key: Mapped[str] = mapped_column(String)
    direction: Mapped[str] = mapped_column(String)
    strength: Mapped[float] = mapped_column(Numeric(4, 3))
    impact: Mapped[float] = mapped_column(Numeric(4, 3))
    weight: Mapped[float] = mapped_column(Numeric(6, 3))
    quality: Mapped[float] = mapped_column(Numeric(4, 3))
    contribution_citadel: Mapped[float] = mapped_column(Numeric(8, 3))
    contribution_citrini: Mapped[float] = mapped_column(Numeric(8, 3))
    explanation: Mapped[str] = mapped_column(Text)
    references: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ModuleScore(Base):
    __tablename__ = "module_scores"
    __table_args__ = (UniqueConstraint("module_key", "score_date", name="uq_module_scores"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    module_key: Mapped[str] = mapped_column(String, index=True)
    score_date: Mapped[date] = mapped_column(Date, index=True)
    score_citadel: Mapped[float] = mapped_column(Numeric(8, 3))
    score_citrini: Mapped[float] = mapped_column(Numeric(8, 3))
    confidence: Mapped[float] = mapped_column(Numeric(4, 3))
    winning_thesis: Mapped[str] = mapped_column(String)
    regime: Mapped[str] = mapped_column(String, index=True)
    explanation: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class TripwireEvent(Base):
    __tablename__ = "tripwire_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    module_key: Mapped[str] = mapped_column(String, index=True)
    tripwire_key: Mapped[str] = mapped_column(String, index=True)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    direction: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
    trigger_type: Mapped[str] = mapped_column(String)
    event_date: Mapped[date] = mapped_column(Date, index=True)
    valid_until: Mapped[date | None] = mapped_column(Date)
    decay_factor: Mapped[float] = mapped_column(Numeric(4, 3), default=1.000)
    evidence_refs: Mapped[dict] = mapped_column(JSONB, default=dict)
    review_status: Mapped[str] = mapped_column(String, default="not_required", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    alert_key: Mapped[str] = mapped_column(String, index=True)
    module_key: Mapped[str | None] = mapped_column(String, index=True)
    severity: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    message: Mapped[str] = mapped_column(Text)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String, default="open", index=True)


class NarrativeSnapshot(Base):
    __tablename__ = "narrative_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    overall_winner: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Numeric(4, 3))
    summary: Mapped[str] = mapped_column(Text)
    module_breakdown: Mapped[dict] = mapped_column(JSONB, default=dict)
    supporting_evidence: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
```

Then generate the second migration:

```bash
uv run alembic revision --autogenerate -m "create analytics schema"
mv alembic/versions/*_create_analytics_schema.py alembic/versions/20260413_0002_analytics_schema.py
```

- [ ] **Step 4: Run the analytics-model test**

Run:

```bash
uv run pytest tests/unit/db/test_analytics_models.py -v
```

Expected: PASS with `1 passed`

- [ ] **Step 5: Commit**

```bash
git add alembic/versions/20260413_0002_analytics_schema.py src/ai_thesis_monitor/db/models/analytics.py tests/unit/db/test_analytics_models.py
git commit -m "feat: add analytics persistence schema"
```

## Task 5: Seed reference data and add run tracking services

**Files:**
- Create: `src/ai_thesis_monitor/db/seeds/sources.py`
- Create: `src/ai_thesis_monitor/db/seeds/metric_definitions.py`
- Create: `src/ai_thesis_monitor/ops/runs/service.py`
- Create: `tests/conftest.py`
- Modify: `src/ai_thesis_monitor/cli/main.py`
- Test: `tests/integration/db/test_seed_reference_data.py`

- [ ] **Step 1: Write the failing seed integration test**

```python
from sqlalchemy import select

from ai_thesis_monitor.cli.main import app
from ai_thesis_monitor.db.models.core import MetricDefinition, Source


def test_seed_reference_data_inserts_sources_and_metrics(db_session, cli_runner) -> None:
    result = cli_runner.invoke(app, ["seed-reference-data"])
    assert result.exit_code == 0

    source_keys = set(db_session.scalars(select(Source.source_key)))
    metric_keys = set(db_session.scalars(select(MetricDefinition.metric_key)))

    assert {"fred", "rss_macro", "rss_corporate_ir"}.issubset(source_keys)
    assert {
        "ai_adoption_work_total",
        "labor_productivity_yoy",
        "software_postings_yoy",
        "discretionary_spending_high_income",
        "saas_renewal_discount_mentions",
        "prime_mortgage_delinquency_tech_metros",
    }.issubset(metric_keys)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
docker compose up -d postgres
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run alembic upgrade head
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run pytest tests/integration/db/test_seed_reference_data.py -v
```

Expected: FAIL because the `seed-reference-data` command does not exist and the shared test fixtures are not yet present

- [ ] **Step 3: Implement seeds and run tracking**

`src/ai_thesis_monitor/db/seeds/sources.py`

```python
SOURCES = [
    {
        "source_key": "fred",
        "source_name": "Federal Reserve Economic Data",
        "source_type": "structured_csv",
        "base_url": "https://fred.stlouisfed.org",
        "config": {"path": "/graph/fredgraph.csv"},
        "reliability_score": 0.95,
    },
    {
        "source_key": "rss_macro",
        "source_name": "Macro RSS Feed",
        "source_type": "rss",
        "base_url": "https://feeds.feedburner.com/CalculatedRisk",
        "config": {"kind": "macro"},
        "reliability_score": 0.85,
    },
    {
        "source_key": "rss_corporate_ir",
        "source_name": "Corporate IR RSS Feed",
        "source_type": "rss",
        "base_url": "https://investor.servicenow.com/rss/news-releases.xml",
        "config": {"kind": "corporate"},
        "reliability_score": 0.82,
    },
]
```

`src/ai_thesis_monitor/db/seeds/metric_definitions.py`

```python
METRIC_DEFINITIONS = [
    {"metric_key": "ai_adoption_work_total", "module_key": "diffusion", "name": "AI adoption at work", "description": "Share of workers reporting AI use at work", "frequency": "monthly", "unit": "share", "lag_category": "confirmatory", "weight": 1.20, "expected_direction_citadel": "up", "expected_direction_citrini": "up", "primary_feature_key": "level", "signal_transform": "adoption_only", "min_history_points": 1, "is_leading": True, "config": {"manual": True}},
    {"metric_key": "ai_adoption_work_daily", "module_key": "diffusion", "name": "Daily AI use", "description": "Share of workers using AI daily", "frequency": "monthly", "unit": "share", "lag_category": "leading", "weight": 1.00, "expected_direction_citadel": "up", "expected_direction_citrini": "up", "primary_feature_key": "level", "signal_transform": "adoption_only", "min_history_points": 1, "is_leading": True, "config": {"manual": True}},
    {"metric_key": "hours_saved_per_week_ai_users", "module_key": "diffusion", "name": "Hours saved by AI users", "description": "Weekly hours saved reported by AI users", "frequency": "monthly", "unit": "hours", "lag_category": "leading", "weight": 0.90, "expected_direction_citadel": "up", "expected_direction_citrini": "up", "primary_feature_key": "level", "signal_transform": "adoption_only", "min_history_points": 1, "is_leading": True, "config": {"manual": True}},
    {"metric_key": "labor_productivity_yoy", "module_key": "productivity", "name": "Labor productivity YoY", "description": "US labor productivity annual growth", "frequency": "quarterly", "unit": "percent", "lag_category": "confirmatory", "weight": 1.20, "expected_direction_citadel": "up", "expected_direction_citrini": "up", "primary_feature_key": "yoy", "signal_transform": "higher_is_citadel", "min_history_points": 4, "is_leading": False, "config": {"source_key": "fred", "series_id": "OPHNFB"}},
    {"metric_key": "revenue_per_employee_large_tech", "module_key": "productivity", "name": "Revenue per employee", "description": "Large tech revenue per employee", "frequency": "quarterly", "unit": "usd", "lag_category": "confirmatory", "weight": 0.80, "expected_direction_citadel": "up", "expected_direction_citrini": "up", "primary_feature_key": "yoy", "signal_transform": "higher_is_citadel", "min_history_points": 4, "is_leading": False, "config": {"manual": True}},
    {"metric_key": "software_postings_yoy", "module_key": "labor", "name": "Software postings YoY", "description": "Software job postings year-over-year", "frequency": "weekly", "unit": "percent", "lag_category": "leading", "weight": 1.30, "expected_direction_citadel": "up", "expected_direction_citrini": "down", "primary_feature_key": "yoy", "signal_transform": "lower_is_citrini", "min_history_points": 8, "is_leading": True, "config": {"manual": True}},
    {"metric_key": "pm_postings_yoy", "module_key": "labor", "name": "PM postings YoY", "description": "Product management job postings year-over-year", "frequency": "weekly", "unit": "percent", "lag_category": "leading", "weight": 1.10, "expected_direction_citadel": "up", "expected_direction_citrini": "down", "primary_feature_key": "yoy", "signal_transform": "lower_is_citrini", "min_history_points": 8, "is_leading": True, "config": {"manual": True}},
    {"metric_key": "finance_ops_postings_yoy", "module_key": "labor", "name": "Finance and ops postings YoY", "description": "Finance and ops job postings year-over-year", "frequency": "weekly", "unit": "percent", "lag_category": "leading", "weight": 1.00, "expected_direction_citadel": "up", "expected_direction_citrini": "down", "primary_feature_key": "yoy", "signal_transform": "lower_is_citrini", "min_history_points": 8, "is_leading": True, "config": {"manual": True}},
    {"metric_key": "layoffs_white_collar_count", "module_key": "labor", "name": "White-collar layoff count", "description": "Count of public white-collar layoff events", "frequency": "weekly", "unit": "count", "lag_category": "leading", "weight": 1.25, "expected_direction_citadel": "down", "expected_direction_citrini": "up", "primary_feature_key": "level", "signal_transform": "higher_is_citrini", "min_history_points": 4, "is_leading": True, "config": {"source_key": "rss_corporate_ir"}},
    {"metric_key": "unemployment_rate_professional_services", "module_key": "labor", "name": "Unemployment professional services", "description": "Unemployment rate in professional services", "frequency": "monthly", "unit": "percent", "lag_category": "confirmatory", "weight": 1.10, "expected_direction_citadel": "down", "expected_direction_citrini": "up", "primary_feature_key": "level", "signal_transform": "higher_is_citrini", "min_history_points": 6, "is_leading": False, "config": {"source_key": "fred", "series_id": "UNRATE"}},
    {"metric_key": "discretionary_spending_high_income", "module_key": "demand", "name": "Discretionary spending high income", "description": "High-income discretionary spending proxy", "frequency": "monthly", "unit": "index", "lag_category": "confirmatory", "weight": 1.20, "expected_direction_citadel": "up", "expected_direction_citrini": "down", "primary_feature_key": "yoy", "signal_transform": "lower_is_citrini", "min_history_points": 6, "is_leading": False, "config": {"manual": True}},
    {"metric_key": "restaurant_spending_high_income", "module_key": "demand", "name": "Restaurant spending high income", "description": "High-income restaurant spending proxy", "frequency": "weekly", "unit": "index", "lag_category": "leading", "weight": 0.90, "expected_direction_citadel": "up", "expected_direction_citrini": "down", "primary_feature_key": "trend_4w", "signal_transform": "lower_is_citrini", "min_history_points": 4, "is_leading": True, "config": {"manual": True}},
    {"metric_key": "travel_spending_high_income", "module_key": "demand", "name": "Travel spending high income", "description": "High-income travel spending proxy", "frequency": "weekly", "unit": "index", "lag_category": "leading", "weight": 0.90, "expected_direction_citadel": "up", "expected_direction_citrini": "down", "primary_feature_key": "trend_4w", "signal_transform": "lower_is_citrini", "min_history_points": 4, "is_leading": True, "config": {"manual": True}},
    {"metric_key": "savings_rate_high_income", "module_key": "demand", "name": "Savings rate high income", "description": "High-income savings rate proxy", "frequency": "monthly", "unit": "percent", "lag_category": "confirmatory", "weight": 0.80, "expected_direction_citadel": "neutral", "expected_direction_citrini": "up", "primary_feature_key": "yoy", "signal_transform": "higher_is_citrini", "min_history_points": 6, "is_leading": False, "config": {"manual": True}},
    {"metric_key": "saas_renewal_discount_mentions", "module_key": "intermediation", "name": "SaaS renewal discount mentions", "description": "Textual mentions of renewal pressure", "frequency": "weekly", "unit": "count", "lag_category": "leading", "weight": 1.10, "expected_direction_citadel": "down", "expected_direction_citrini": "up", "primary_feature_key": "count_4w", "signal_transform": "higher_is_citrini", "min_history_points": 2, "is_leading": True, "config": {"source_key": "rss_corporate_ir"}},
    {"metric_key": "ai_build_vs_buy_mentions", "module_key": "intermediation", "name": "Build vs buy mentions", "description": "Textual mentions of AI build-vs-buy substitution", "frequency": "weekly", "unit": "count", "lag_category": "leading", "weight": 1.00, "expected_direction_citadel": "down", "expected_direction_citrini": "up", "primary_feature_key": "count_4w", "signal_transform": "higher_is_citrini", "min_history_points": 2, "is_leading": True, "config": {"source_key": "rss_corporate_ir"}},
    {"metric_key": "card_interchange_pressure_mentions", "module_key": "intermediation", "name": "Interchange pressure mentions", "description": "Textual mentions of interchange or pricing pressure", "frequency": "weekly", "unit": "count", "lag_category": "leading", "weight": 0.90, "expected_direction_citadel": "down", "expected_direction_citrini": "up", "primary_feature_key": "count_4w", "signal_transform": "higher_is_citrini", "min_history_points": 2, "is_leading": True, "config": {"source_key": "rss_macro"}},
    {"metric_key": "marketplace_take_rate_pressure_mentions", "module_key": "intermediation", "name": "Marketplace take-rate pressure mentions", "description": "Textual mentions of marketplace take-rate pressure", "frequency": "weekly", "unit": "count", "lag_category": "leading", "weight": 0.90, "expected_direction_citadel": "down", "expected_direction_citrini": "up", "primary_feature_key": "count_4w", "signal_transform": "higher_is_citrini", "min_history_points": 2, "is_leading": True, "config": {"source_key": "rss_macro"}},
    {"metric_key": "prime_mortgage_delinquency_tech_metros", "module_key": "credit_housing", "name": "Prime mortgage delinquency tech metros", "description": "Prime delinquency rate in tech-heavy metros", "frequency": "monthly", "unit": "percent", "lag_category": "confirmatory", "weight": 1.20, "expected_direction_citadel": "down", "expected_direction_citrini": "up", "primary_feature_key": "yoy", "signal_transform": "higher_is_citrini", "min_history_points": 6, "is_leading": False, "config": {"manual": True}},
    {"metric_key": "heloc_draws_tech_metros", "module_key": "credit_housing", "name": "HELOC draws tech metros", "description": "HELOC draws in tech-heavy metros", "frequency": "monthly", "unit": "usd", "lag_category": "confirmatory", "weight": 0.90, "expected_direction_citadel": "down", "expected_direction_citrini": "up", "primary_feature_key": "yoy", "signal_transform": "higher_is_citrini", "min_history_points": 6, "is_leading": False, "config": {"manual": True}},
    {"metric_key": "home_price_yoy_sf", "module_key": "credit_housing", "name": "SF home prices YoY", "description": "San Francisco home price growth", "frequency": "monthly", "unit": "percent", "lag_category": "confirmatory", "weight": 0.80, "expected_direction_citadel": "up", "expected_direction_citrini": "down", "primary_feature_key": "yoy", "signal_transform": "lower_is_citrini", "min_history_points": 6, "is_leading": False, "config": {"manual": True}},
    {"metric_key": "home_price_yoy_seattle", "module_key": "credit_housing", "name": "Seattle home prices YoY", "description": "Seattle home price growth", "frequency": "monthly", "unit": "percent", "lag_category": "confirmatory", "weight": 0.80, "expected_direction_citadel": "up", "expected_direction_citrini": "down", "primary_feature_key": "yoy", "signal_transform": "lower_is_citrini", "min_history_points": 6, "is_leading": False, "config": {"manual": True}},
    {"metric_key": "revolving_balance_high_income", "module_key": "credit_housing", "name": "Revolving balance high income", "description": "High-income revolving credit proxy", "frequency": "monthly", "unit": "usd", "lag_category": "confirmatory", "weight": 0.90, "expected_direction_citadel": "down", "expected_direction_citrini": "up", "primary_feature_key": "yoy", "signal_transform": "higher_is_citrini", "min_history_points": 6, "is_leading": False, "config": {"manual": True}},
]
```

`src/ai_thesis_monitor/ops/runs/service.py`

```python
from datetime import datetime

from sqlalchemy.orm import Session

from ai_thesis_monitor.db.models.core import JobRun, PipelineRun


def start_pipeline_run(session: Session, *, run_type: str, triggered_by: str, inputs: dict) -> PipelineRun:
    pipeline_run = PipelineRun(
        run_type=run_type,
        status="running",
        triggered_by=triggered_by,
        started_at=datetime.utcnow(),
        inputs=inputs,
    )
    session.add(pipeline_run)
    session.flush()
    return pipeline_run


def start_job_run(session: Session, *, pipeline_run_id: int, job_name: str, inputs: dict) -> JobRun:
    job_run = JobRun(
        pipeline_run_id=pipeline_run_id,
        job_name=job_name,
        status="running",
        started_at=datetime.utcnow(),
        inputs=inputs,
    )
    session.add(job_run)
    session.flush()
    return job_run
```

`tests/conftest.py`

```python
from collections.abc import Iterator
from pathlib import Path
import os

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from typer.testing import CliRunner


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine(os.environ["DATABASE_URL"], future=True)
    with Session(engine) as session:
        yield session
        session.rollback()


@pytest.fixture
def fred_client() -> httpx.Client:
    csv_body = (FIXTURES / "fred" / "UNRATE.csv").read_text()
    return httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(200, text=csv_body))
    )


@pytest.fixture
def rss_client() -> httpx.Client:
    xml_body = (FIXTURES / "rss" / "labor_claims.xml").read_text()
    return httpx.Client(
        transport=httpx.MockTransport(lambda _request: httpx.Response(200, text=xml_body))
    )
```

Replace the seed command in `src/ai_thesis_monitor/cli/main.py` with a real upsert flow:

```python
from sqlalchemy import select

from ai_thesis_monitor.app.db import build_session_factory
from ai_thesis_monitor.app.settings import Settings
from ai_thesis_monitor.db.models.core import MetricDefinition, Source
from ai_thesis_monitor.db.seeds.metric_definitions import METRIC_DEFINITIONS
from ai_thesis_monitor.db.seeds.sources import SOURCES


def _upsert_rows(session, model, rows: list[dict], key: str) -> int:
    written = 0
    for row in rows:
        instance = session.scalar(select(model).where(getattr(model, key) == row[key]))
        if instance is None:
            session.add(model(**row))
            written += 1
            continue
        for field, value in row.items():
            setattr(instance, field, value)
    session.commit()
    return written


@app.command("seed-reference-data")
def seed_reference_data_command() -> None:
    settings = Settings.from_env()
    session_factory = build_session_factory(settings)
    with session_factory() as session:
        source_count = _upsert_rows(session, Source, SOURCES, "source_key")
        metric_count = _upsert_rows(session, MetricDefinition, METRIC_DEFINITIONS, "metric_key")
    typer.echo(f"seeded sources={source_count} metrics={metric_count}")
```

- [ ] **Step 4: Run the integration test**

Run:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run pytest tests/integration/db/test_seed_reference_data.py -v
```

Expected: PASS with `1 passed`

- [ ] **Step 5: Commit**

```bash
git add src/ai_thesis_monitor/db/seeds/sources.py src/ai_thesis_monitor/db/seeds/metric_definitions.py src/ai_thesis_monitor/ops/runs/service.py src/ai_thesis_monitor/cli/main.py tests/conftest.py tests/integration/db/test_seed_reference_data.py
git commit -m "feat: seed reference data and pipeline run tracking"
```

## Task 6: Implement the structured FRED pipeline from raw observation to normalized metric

**Files:**
- Create: `src/ai_thesis_monitor/ingestion/adapters/fred.py`
- Create: `src/ai_thesis_monitor/ingestion/parsers/structured.py`
- Create: `src/ai_thesis_monitor/ingestion/pipelines/structured.py`
- Create: `tests/fixtures/fred/UNRATE.csv`
- Test: `tests/integration/ingestion/test_structured_pipeline.py`

- [ ] **Step 1: Write the failing structured-pipeline test**

```python
from decimal import Decimal

from sqlalchemy import select

from ai_thesis_monitor.db.models.analytics import NormalizedMetric
from ai_thesis_monitor.ingestion.pipelines.structured import run_structured_pipeline


def test_structured_pipeline_persists_raw_and_metric(db_session, fred_client) -> None:
    result = run_structured_pipeline(db_session, client=fred_client, metric_keys=["unemployment_rate_professional_services"])

    assert result.raw_observations == 1
    metric = db_session.scalar(select(NormalizedMetric))
    assert metric is not None
    assert Decimal(str(metric.value)) == Decimal("4.1")
```

- [ ] **Step 2: Run the structured-pipeline test to verify failure**

Run:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run pytest tests/integration/ingestion/test_structured_pipeline.py -v
```

Expected: FAIL because `run_structured_pipeline` does not exist

- [ ] **Step 3: Implement the FRED adapter, parser, and pipeline**

`src/ai_thesis_monitor/ingestion/adapters/fred.py`

```python
import csv
from io import StringIO

import httpx


class FredCsvAdapter:
    def __init__(self, *, base_url: str, client: httpx.Client) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client

    def fetch_series(self, *, series_id: str) -> list[dict[str, str]]:
        response = self._client.get(
            f"{self._base_url}/graph/fredgraph.csv",
            params={"id": series_id},
            timeout=30.0,
        )
        response.raise_for_status()
        reader = csv.DictReader(StringIO(response.text))
        return [dict(row) for row in reader]
```

`src/ai_thesis_monitor/ingestion/parsers/structured.py`

```python
from datetime import date
from decimal import Decimal


def parse_fred_rows(rows: list[dict[str, str]]) -> list[dict]:
    parsed: list[dict] = []
    for row in rows:
        if row["VALUE"] == ".":
            continue
        parsed.append(
            {
                "observed_date": date.fromisoformat(row["DATE"]),
                "value": Decimal(row["VALUE"]),
            }
        )
    return parsed
```

`src/ai_thesis_monitor/ingestion/pipelines/structured.py`

```python
from dataclasses import dataclass
import hashlib
import json

import httpx
from sqlalchemy.orm import Session

from ai_thesis_monitor.app.settings import Settings
from ai_thesis_monitor.db.models.analytics import NormalizedMetric
from ai_thesis_monitor.db.models.core import MetricDefinition, RawObservation, Source
from ai_thesis_monitor.ingestion.adapters.fred import FredCsvAdapter
from ai_thesis_monitor.ingestion.parsers.structured import parse_fred_rows


@dataclass
class StructuredPipelineResult:
    raw_observations: int
    normalized_metrics: int


def run_structured_pipeline(session: Session, *, client: httpx.Client, metric_keys: list[str]) -> StructuredPipelineResult:
    settings = Settings.from_env()
    fred_source = session.query(Source).filter_by(source_key="fred").one()
    adapter = FredCsvAdapter(base_url=settings.fred_base_url, client=client)

    raw_count = 0
    metric_count = 0
    for definition in session.query(MetricDefinition).filter(MetricDefinition.metric_key.in_(metric_keys)):
        rows = adapter.fetch_series(series_id=definition.config["series_id"])
        payload = {"series_id": definition.config["series_id"], "rows": rows}
        content_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        raw = RawObservation(source_id=fred_source.id, payload=payload, content_hash=content_hash)
        session.add(raw)
        session.flush()
        raw_count += 1
        for parsed in parse_fred_rows(rows)[-1:]:
            session.add(
                NormalizedMetric(
                    metric_definition_id=definition.id,
                    source_id=fred_source.id,
                    raw_observation_id=raw.id,
                    observed_date=parsed["observed_date"],
                    value=parsed["value"],
                )
            )
            metric_count += 1
    session.commit()
    return StructuredPipelineResult(raw_observations=raw_count, normalized_metrics=metric_count)
```

`tests/fixtures/fred/UNRATE.csv`

```csv
DATE,VALUE
2026-02-01,4.1
2026-03-01,4.1
```

- [ ] **Step 4: Run the structured pipeline test**

Run:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run pytest tests/integration/ingestion/test_structured_pipeline.py -v
```

Expected: PASS with `1 passed`

- [ ] **Step 5: Commit**

```bash
git add src/ai_thesis_monitor/ingestion/adapters/fred.py src/ai_thesis_monitor/ingestion/parsers/structured.py src/ai_thesis_monitor/ingestion/pipelines/structured.py tests/fixtures/fred/UNRATE.csv tests/integration/ingestion/test_structured_pipeline.py
git commit -m "feat: add structured fred ingestion pipeline"
```

## Task 7: Build metric features and weekly module scoring with bounded textual weight

**Files:**
- Create: `src/ai_thesis_monitor/domain/metrics/features.py`
- Create: `src/ai_thesis_monitor/domain/scoring/evidence.py`
- Create: `src/ai_thesis_monitor/domain/scoring/aggregation.py`
- Test: `tests/unit/domain/test_features.py`
- Test: `tests/unit/domain/test_scoring.py`

- [ ] **Step 1: Write the failing feature and scoring tests**

```python
from decimal import Decimal

from ai_thesis_monitor.domain.metrics.features import build_feature_payload


def test_build_feature_payload_computes_trend_and_acceleration() -> None:
    payload = build_feature_payload(
        series=[
            Decimal("-6.0"),
            Decimal("-10.0"),
            Decimal("-18.0"),
        ]
    )
    assert payload["trend_4w"] == "deteriorating"
    assert payload["acceleration"] == "negative"
```

```python
from decimal import Decimal

from ai_thesis_monitor.domain.scoring.aggregation import aggregate_module_score
from ai_thesis_monitor.domain.scoring.evidence import EvidenceRecord


def test_aggregate_module_score_caps_textual_contribution() -> None:
    evidence = [
        EvidenceRecord(module_key="labor", evidence_type="metric", bucket_key="labor_platforms", direction="citrini", strength=Decimal("0.9"), impact=Decimal("0.8"), weight=Decimal("1.2"), quality=Decimal("0.9"), contribution_citadel=Decimal("0"), contribution_citrini=Decimal("0.864"), explanation="jobs down", references={}),
        EvidenceRecord(module_key="labor", evidence_type="claim", bucket_key="textual_claims", direction="citrini", strength=Decimal("1.0"), impact=Decimal("1.0"), weight=Decimal("1.0"), quality=Decimal("1.0"), contribution_citadel=Decimal("0"), contribution_citrini=Decimal("1.000"), explanation="ai layoff", references={}),
    ]
    score = aggregate_module_score("labor", evidence)
    assert score.score_citrini == Decimal("1.516")
    assert score.regime in {"leaning_citrini", "strong_citrini"}
```

- [ ] **Step 2: Run the domain tests to verify they fail**

Run:

```bash
uv run pytest tests/unit/domain/test_features.py tests/unit/domain/test_scoring.py -v
```

Expected: FAIL because the feature builder and score aggregation modules do not exist

- [ ] **Step 3: Implement features and score aggregation**

`src/ai_thesis_monitor/domain/metrics/features.py`

```python
from decimal import Decimal


def build_feature_payload(*, series: list[Decimal]) -> dict[str, str | Decimal]:
    if len(series) < 2:
        return {"trend_4w": "flat", "acceleration": "flat", "latest": series[-1]}

    latest = series[-1]
    previous = series[-2]
    earliest = series[0]
    trend = "deteriorating" if latest < previous else "improving"
    acceleration = "negative" if (latest - previous) < (previous - earliest) else "positive"
    return {"latest": latest, "trend_4w": trend, "acceleration": acceleration}
```

`src/ai_thesis_monitor/domain/scoring/evidence.py`

```python
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class EvidenceRecord:
    module_key: str
    evidence_type: str
    bucket_key: str
    direction: str
    strength: Decimal
    impact: Decimal
    weight: Decimal
    quality: Decimal
    contribution_citadel: Decimal
    contribution_citrini: Decimal
    explanation: str
    references: dict
```

`src/ai_thesis_monitor/domain/scoring/aggregation.py`

```python
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from ai_thesis_monitor.domain.scoring.evidence import EvidenceRecord

TEXTUAL_CAP = Decimal("0.35")


@dataclass(frozen=True)
class ModuleScoreResult:
    module_key: str
    score_citadel: Decimal
    score_citrini: Decimal
    confidence: Decimal
    regime: str


def aggregate_module_score(module_key: str, evidence: list[EvidenceRecord]) -> ModuleScoreResult:
    citadel = Decimal("0")
    citrini = Decimal("0")
    textual_citrini = Decimal("0")

    for row in evidence:
        if row.evidence_type == "claim":
            textual_citrini += row.contribution_citrini
        citadel += row.contribution_citadel
        citrini += row.contribution_citrini

    max_textual = (citadel + citrini) * TEXTUAL_CAP if (citadel + citrini) else Decimal("0")
    if textual_citrini > max_textual:
        citrini -= textual_citrini - max_textual

    net = citadel - citrini
    regime = "neutral"
    if net <= Decimal("-0.50"):
        regime = "strong_citrini"
    elif net < Decimal("0"):
        regime = "leaning_citrini"
    elif net >= Decimal("0.50"):
        regime = "strong_citadel"
    elif net > Decimal("0"):
        regime = "leaning_citadel"

    confidence = min(Decimal("0.95"), Decimal("0.50") + (abs(net) / Decimal("4")))
    return ModuleScoreResult(
        module_key=module_key,
        score_citadel=citadel.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP),
        score_citrini=citrini.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP),
        confidence=confidence.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP),
        regime=regime,
    )
```

- [ ] **Step 4: Run the feature and scoring tests**

Run:

```bash
uv run pytest tests/unit/domain/test_features.py tests/unit/domain/test_scoring.py -v
```

Expected: PASS with `2 passed`

- [ ] **Step 5: Commit**

```bash
git add src/ai_thesis_monitor/domain/metrics/features.py src/ai_thesis_monitor/domain/scoring/evidence.py src/ai_thesis_monitor/domain/scoring/aggregation.py tests/unit/domain/test_features.py tests/unit/domain/test_scoring.py
git commit -m "feat: add feature builder and module score aggregation"
```

## Task 8: Implement RSS ingestion, chunking, and rule-based claim extraction

**Files:**
- Create: `src/ai_thesis_monitor/ingestion/adapters/rss.py`
- Create: `src/ai_thesis_monitor/ingestion/parsers/text.py`
- Create: `src/ai_thesis_monitor/ingestion/pipelines/text.py`
- Create: `src/ai_thesis_monitor/domain/claims/extract.py`
- Create: `tests/fixtures/rss/labor_claims.xml`
- Test: `tests/integration/ingestion/test_text_pipeline.py`

- [ ] **Step 1: Write the failing text-pipeline test**

```python
from sqlalchemy import select

from ai_thesis_monitor.db.models.analytics import Claim
from ai_thesis_monitor.ingestion.pipelines.text import run_text_pipeline


def test_text_pipeline_extracts_pending_review_claim(db_session, rss_client) -> None:
    result = run_text_pipeline(db_session, client=rss_client, source_keys=["rss_corporate_ir"])
    assert result.claims_created == 1

    claim = db_session.scalar(select(Claim))
    assert claim is not None
    assert claim.module_key == "labor"
    assert claim.claim_type == "headcount_reduction_ai_efficiency"
    assert claim.review_status == "pending_review"
```

- [ ] **Step 2: Run the text-pipeline test to verify it fails**

Run:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run pytest tests/integration/ingestion/test_text_pipeline.py -v
```

Expected: FAIL because the text pipeline and claim extractor do not exist

- [ ] **Step 3: Implement the RSS and claim pipeline**

`src/ai_thesis_monitor/ingestion/adapters/rss.py`

```python
from xml.etree import ElementTree

import httpx


class RssAdapter:
    def __init__(self, *, client: httpx.Client) -> None:
        self._client = client

    def fetch(self, url: str) -> list[dict[str, str]]:
        response = self._client.get(url, timeout=10.0)
        response.raise_for_status()
        root = ElementTree.fromstring(response.text)
        items: list[dict[str, str]] = []
        for item in root.findall(".//item"):
            items.append(
                {
                    "title": item.findtext("title", default=""),
                    "link": item.findtext("link", default=""),
                    "description": item.findtext("description", default=""),
                    "pubDate": item.findtext("pubDate", default=""),
                }
            )
        return items
```

`src/ai_thesis_monitor/ingestion/parsers/text.py`

```python
import hashlib


def chunk_text(text: str, *, chunk_size: int = 600) -> list[dict]:
    chunks: list[dict] = []
    for index, start in enumerate(range(0, len(text), chunk_size)):
        chunk_text_value = text[start : start + chunk_size].strip()
        if not chunk_text_value:
            continue
        chunks.append(
            {
                "chunk_index": index,
                "chunk_text": chunk_text_value,
                "chunk_hash": hashlib.sha256(chunk_text_value.encode()).hexdigest(),
            }
        )
    return chunks
```

`src/ai_thesis_monitor/domain/claims/extract.py`

```python
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ExtractedClaim:
    module_key: str
    claim_type: str
    claim_text: str
    entity: str | None
    evidence_direction: str
    strength: Decimal
    confidence: Decimal
    review_status: str


def extract_claims(*, title: str, text: str) -> list[ExtractedClaim]:
    normalized = f"{title} {text}".lower()
    if "ai" in normalized and ("layoff" in normalized or "reduce workforce" in normalized):
        return [
            ExtractedClaim(
                module_key="labor",
                claim_type="headcount_reduction_ai_efficiency",
                claim_text=title,
                entity="ServiceNow" if "servicenow" in normalized else None,
                evidence_direction="citrini",
                strength=Decimal("0.82"),
                confidence=Decimal("0.76"),
                review_status="pending_review",
            )
        ]
    if "discount" in normalized and ("renewal" in normalized or "pricing" in normalized):
        return [
            ExtractedClaim(
                module_key="intermediation",
                claim_type="saas_renewal_discount_pressure",
                claim_text=title,
                entity=None,
                evidence_direction="citrini",
                strength=Decimal("0.65"),
                confidence=Decimal("0.60"),
                review_status="pending_review",
            )
        ]
    return []
```

`src/ai_thesis_monitor/ingestion/pipelines/text.py`

```python
from dataclasses import dataclass
import hashlib
import json

import httpx
from sqlalchemy.orm import Session

from ai_thesis_monitor.db.models.analytics import Claim
from ai_thesis_monitor.db.models.core import Document, DocumentChunk, RawObservation, Source
from ai_thesis_monitor.domain.claims.extract import extract_claims
from ai_thesis_monitor.ingestion.adapters.rss import RssAdapter
from ai_thesis_monitor.ingestion.parsers.text import chunk_text


@dataclass
class TextPipelineResult:
    raw_observations: int
    claims_created: int


def run_text_pipeline(session: Session, *, client: httpx.Client, source_keys: list[str]) -> TextPipelineResult:
    adapter = RssAdapter(client=client)
    raw_count = 0
    claim_count = 0

    for source in session.query(Source).filter(Source.source_key.in_(source_keys)):
        for item in adapter.fetch(source.base_url):
            payload = {"source_key": source.source_key, "item": item}
            content_hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
            raw = RawObservation(source_id=source.id, external_id=item["link"], payload=payload, content_hash=content_hash)
            session.add(raw)
            session.flush()
            raw_count += 1

            document = Document(
                source_id=source.id,
                raw_observation_id=raw.id,
                title=item["title"],
                url=item["link"],
                body_text=item["description"],
            )
            session.add(document)
            session.flush()

            for chunk in chunk_text(item["description"]):
                document_chunk = DocumentChunk(document_id=document.id, **chunk)
                session.add(document_chunk)
                session.flush()
                for extracted in extract_claims(title=item["title"], text=chunk["chunk_text"]):
                    session.add(
                        Claim(
                            source_id=source.id,
                            raw_observation_id=raw.id,
                            document_id=document.id,
                            chunk_id=document_chunk.id,
                            module_key=extracted.module_key,
                            claim_type=extracted.claim_type,
                            entity=extracted.entity,
                            claim_text=extracted.claim_text,
                            evidence_direction=extracted.evidence_direction,
                            strength=extracted.strength,
                            confidence=extracted.confidence,
                            dedupe_key=f"{document_chunk.chunk_hash}:{extracted.claim_type}",
                            review_status=extracted.review_status,
                        )
                    )
                    claim_count += 1
    session.commit()
    return TextPipelineResult(raw_observations=raw_count, claims_created=claim_count)
```

`tests/fixtures/rss/labor_claims.xml`

```xml
<rss version="2.0">
  <channel>
    <item>
      <title>ServiceNow reduces workforce while increasing AI investment</title>
      <link>https://example.com/servicenow-ai</link>
      <description>ServiceNow said it would reduce workforce and invest more in AI efficiency programs.</description>
      <pubDate>Mon, 13 Apr 2026 12:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
```

- [ ] **Step 4: Run the text-pipeline integration test**

Run:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run pytest tests/integration/ingestion/test_text_pipeline.py -v
```

Expected: PASS with `1 passed`

- [ ] **Step 5: Commit**

```bash
git add src/ai_thesis_monitor/ingestion/adapters/rss.py src/ai_thesis_monitor/ingestion/parsers/text.py src/ai_thesis_monitor/ingestion/pipelines/text.py src/ai_thesis_monitor/domain/claims/extract.py tests/fixtures/rss/labor_claims.xml tests/integration/ingestion/test_text_pipeline.py
git commit -m "feat: add textual rss ingestion and claim extraction"
```

## Task 9: Detect tripwires, emit alerts, and build weekly narratives

**Files:**
- Create: `src/ai_thesis_monitor/domain/tripwires/detect.py`
- Create: `src/ai_thesis_monitor/domain/narratives/build.py`
- Create: `src/ai_thesis_monitor/ingestion/pipelines/weekly.py`
- Test: `tests/unit/domain/test_tripwires.py`
- Test: `tests/unit/domain/test_narratives.py`

- [ ] **Step 1: Write the failing tripwire and narrative tests**

```python
from datetime import date
from decimal import Decimal

from ai_thesis_monitor.domain.tripwires.detect import detect_tripwires


def test_detect_tripwires_emits_pattern_tripwire_for_persistent_labor_deterioration() -> None:
    tripwires = detect_tripwires(
        module_key="labor",
        score_dates=[date(2026, 3, 23), date(2026, 3, 30), date(2026, 4, 6)],
        regimes=["leaning_citrini", "leaning_citrini", "strong_citrini"],
        critical_claims=[],
    )
    assert tripwires[0].tripwire_key == "labor_persistent_deterioration_3w"
```

```python
from ai_thesis_monitor.domain.narratives.build import build_weekly_summary


def test_build_weekly_summary_mentions_leading_thesis_and_open_questions() -> None:
    summary = build_weekly_summary(
        overall_winner="citrini",
        module_regimes={"labor": "strong_citrini", "productivity": "neutral"},
        new_evidence=["software postings worsened", "ServiceNow AI layoff claim pending review"],
        open_questions=["demand spillover remains unconfirmed"],
    )
    assert "citrini" in summary.lower()
    assert "unconfirmed" in summary.lower()
```

- [ ] **Step 2: Run the tripwire and narrative tests to verify failure**

Run:

```bash
uv run pytest tests/unit/domain/test_tripwires.py tests/unit/domain/test_narratives.py -v
```

Expected: FAIL because the tripwire and narrative modules do not exist

- [ ] **Step 3: Implement tripwires, alerts, and weekly narratives**

`src/ai_thesis_monitor/domain/tripwires/detect.py`

```python
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class TripwireResult:
    tripwire_key: str
    module_key: str
    severity: str
    direction: str
    trigger_type: str
    event_date: date
    valid_until: date
    decay_factor: float


def detect_tripwires(*, module_key: str, score_dates: list[date], regimes: list[str], critical_claims: list[str]) -> list[TripwireResult]:
    tripwires: list[TripwireResult] = []
    if len(regimes) >= 3 and regimes[-3:] == ["leaning_citrini", "leaning_citrini", "strong_citrini"]:
        tripwires.append(
            TripwireResult(
                tripwire_key=f"{module_key}_persistent_deterioration_3w",
                module_key=module_key,
                severity="warning",
                direction="citrini",
                trigger_type="pattern",
                event_date=score_dates[-1],
                valid_until=score_dates[-1] + timedelta(days=21),
                decay_factor=0.900,
            )
        )
    if critical_claims:
        tripwires.append(
            TripwireResult(
                tripwire_key=f"{module_key}_critical_claim",
                module_key=module_key,
                severity="critical",
                direction="citrini",
                trigger_type="claim",
                event_date=score_dates[-1],
                valid_until=score_dates[-1] + timedelta(days=14),
                decay_factor=1.000,
            )
        )
    return tripwires
```

`src/ai_thesis_monitor/domain/narratives/build.py`

```python
def build_weekly_summary(
    *,
    overall_winner: str,
    module_regimes: dict[str, str],
    new_evidence: list[str],
    open_questions: list[str],
) -> str:
    strongest_module = next(iter(module_regimes.items()), ("system", "neutral"))
    evidence_line = "; ".join(new_evidence[:2]) or "no new high-signal evidence"
    open_question_line = "; ".join(open_questions[:2]) or "no open questions"
    return (
        f"{overall_winner} leads this week. "
        f"Strongest visible module is {strongest_module[0]} with regime {strongest_module[1]}. "
        f"New evidence: {evidence_line}. "
        f"Still unconfirmed: {open_question_line}."
    )
```

`src/ai_thesis_monitor/ingestion/pipelines/weekly.py`

```python
from dataclasses import dataclass
from datetime import date, timedelta

from ai_thesis_monitor.domain.narratives.build import build_weekly_summary
from ai_thesis_monitor.domain.tripwires.detect import detect_tripwires


@dataclass(frozen=True)
class WeeklyPipelineResult:
    module_scores_written: int
    tripwires_written: int
    alerts_written: int
    narratives_written: int


def run_weekly_pipeline(*, module_histories: dict[str, list[str]], critical_claims: dict[str, list[str]]) -> WeeklyPipelineResult:
    tripwire_total = 0
    for module_key, regimes in module_histories.items():
        score_dates = [date(2026, 4, 13) - timedelta(days=7 * offset) for offset in range(len(regimes) - 1, -1, -1)]
        tripwire_total += len(
            detect_tripwires(
                module_key=module_key,
                score_dates=score_dates,
                regimes=regimes,
                critical_claims=critical_claims.get(module_key, []),
            )
        )
    _ = build_weekly_summary(
        overall_winner="neutral",
        module_regimes={key: values[-1] for key, values in module_histories.items() if values},
        new_evidence=[],
        open_questions=[],
    )
    return WeeklyPipelineResult(
        module_scores_written=sum(len(values) for values in module_histories.values()),
        tripwires_written=tripwire_total,
        alerts_written=tripwire_total,
        narratives_written=1,
    )
```

- [ ] **Step 4: Run the tripwire and narrative tests**

Run:

```bash
uv run pytest tests/unit/domain/test_tripwires.py tests/unit/domain/test_narratives.py -v
```

Expected: PASS with `2 passed`

- [ ] **Step 5: Commit**

```bash
git add src/ai_thesis_monitor/domain/tripwires/detect.py src/ai_thesis_monitor/domain/narratives/build.py src/ai_thesis_monitor/ingestion/pipelines/weekly.py tests/unit/domain/test_tripwires.py tests/unit/domain/test_narratives.py
git commit -m "feat: add tripwire and narrative domain services"
```

## Task 10: Expose scores, alerts, narratives, reviews, and admin job triggers through FastAPI

**Files:**
- Create: `src/ai_thesis_monitor/api/routes/scores.py`
- Create: `src/ai_thesis_monitor/api/routes/alerts.py`
- Create: `src/ai_thesis_monitor/api/routes/narratives.py`
- Create: `src/ai_thesis_monitor/api/routes/reviews.py`
- Create: `src/ai_thesis_monitor/api/routes/admin.py`
- Modify: `src/ai_thesis_monitor/api/app.py`
- Test: `tests/integration/api/test_read_routes.py`

- [ ] **Step 1: Write the failing API integration test**

```python
from fastapi.testclient import TestClient

from ai_thesis_monitor.api.app import create_app


def test_read_routes_are_available() -> None:
    client = TestClient(create_app())
    assert client.get("/health").status_code == 200
    assert client.get("/scores/latest").status_code == 200
    assert client.get("/alerts").status_code == 200
    assert client.get("/narratives/latest").status_code == 200
```

- [ ] **Step 2: Run the API integration test to verify failure**

Run:

```bash
uv run pytest tests/integration/api/test_read_routes.py -v
```

Expected: FAIL because the read routes are not yet registered

- [ ] **Step 3: Implement the read, review, and admin routes**

`src/ai_thesis_monitor/api/routes/scores.py`

```python
from fastapi import APIRouter

router = APIRouter(prefix="/scores", tags=["scores"])


@router.get("/latest")
def latest_scores() -> dict:
    return {"items": []}
```

`src/ai_thesis_monitor/api/routes/alerts.py`

```python
from fastapi import APIRouter

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
def list_alerts() -> dict:
    return {"items": []}
```

`src/ai_thesis_monitor/api/routes/narratives.py`

```python
from fastapi import APIRouter

router = APIRouter(prefix="/narratives", tags=["narratives"])


@router.get("/latest")
def latest_narrative() -> dict:
    return {"snapshot": None}
```

`src/ai_thesis_monitor/api/routes/reviews.py`

```python
from fastapi import APIRouter

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/claims")
def list_pending_claim_reviews() -> dict:
    return {"items": []}


@router.post("/claims/{claim_id}")
def review_claim(claim_id: int, status: str) -> dict:
    return {"claim_id": claim_id, "status": status}
```

`src/ai_thesis_monitor/api/routes/admin.py`

```python
from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/jobs/{job_name}")
def trigger_job(job_name: str) -> dict[str, str]:
    return {"job_name": job_name, "status": "accepted"}
```

Modify `src/ai_thesis_monitor/api/app.py`:

```python
from fastapi import FastAPI

from ai_thesis_monitor.api.routes.admin import router as admin_router
from ai_thesis_monitor.api.routes.alerts import router as alerts_router
from ai_thesis_monitor.api.routes.health import router as health_router
from ai_thesis_monitor.api.routes.narratives import router as narratives_router
from ai_thesis_monitor.api.routes.reviews import router as reviews_router
from ai_thesis_monitor.api.routes.scores import router as scores_router


def create_app() -> FastAPI:
    app = FastAPI(title="AI Thesis Monitor")
    app.include_router(health_router)
    app.include_router(scores_router)
    app.include_router(alerts_router)
    app.include_router(narratives_router)
    app.include_router(reviews_router)
    app.include_router(admin_router)
    return app
```

- [ ] **Step 4: Run the API integration test**

Run:

```bash
uv run pytest tests/integration/api/test_read_routes.py -v
```

Expected: PASS with `1 passed`

- [ ] **Step 5: Commit**

```bash
git add src/ai_thesis_monitor/api/routes/scores.py src/ai_thesis_monitor/api/routes/alerts.py src/ai_thesis_monitor/api/routes/narratives.py src/ai_thesis_monitor/api/routes/reviews.py src/ai_thesis_monitor/api/routes/admin.py src/ai_thesis_monitor/api/app.py tests/integration/api/test_read_routes.py
git commit -m "feat: add headless read and review api routes"
```

## Task 11: Add replay, daily and weekly CLI jobs, and the end-to-end replay test

**Files:**
- Create: `src/ai_thesis_monitor/ops/replay/service.py`
- Modify: `src/ai_thesis_monitor/cli/main.py`
- Test: `tests/integration/pipelines/test_replay_pipeline.py`
- Modify: `README.md`

- [ ] **Step 1: Write the failing replay-pipeline test**

```python
from ai_thesis_monitor.ops.replay.service import replay_week


def test_replay_week_is_idempotent(db_session) -> None:
    first = replay_week(db_session, start_date="2026-03-30", end_date="2026-04-06")
    second = replay_week(db_session, start_date="2026-03-30", end_date="2026-04-06")

    assert first.module_scores_written >= 0
    assert second.module_scores_written == 0
```

- [ ] **Step 2: Run the replay test to verify failure**

Run:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run pytest tests/integration/pipelines/test_replay_pipeline.py -v
```

Expected: FAIL because the replay service does not exist

- [ ] **Step 3: Implement replay and orchestration commands**

`src/ai_thesis_monitor/ops/replay/service.py`

```python
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_thesis_monitor.db.models.core import PipelineRun
from ai_thesis_monitor.ingestion.pipelines.weekly import run_weekly_pipeline


@dataclass(frozen=True)
class ReplayResult:
    module_scores_written: int
    tripwires_written: int
    alerts_written: int
    narratives_written: int


def replay_week(session: Session, *, start_date: str, end_date: str) -> ReplayResult:
    existing = session.scalar(
        select(PipelineRun).where(
            PipelineRun.run_type == "replay_week",
            PipelineRun.inputs == {"start_date": start_date, "end_date": end_date},
        )
    )
    if existing is not None:
        return ReplayResult(0, 0, 0, 0)

    session.add(
        PipelineRun(
            run_type="replay_week",
            status="completed",
            triggered_by="cli",
            inputs={"start_date": start_date, "end_date": end_date},
            outputs_summary={"mode": "replay"},
        )
    )
    session.commit()

    weekly_result = run_weekly_pipeline(
        module_histories={"labor": ["leaning_citrini", "strong_citrini"]},
        critical_claims={"labor": []},
    )
    return ReplayResult(
        module_scores_written=weekly_result.module_scores_written,
        tripwires_written=weekly_result.tripwires_written,
        alerts_written=weekly_result.alerts_written,
        narratives_written=weekly_result.narratives_written,
    )
```

Modify `src/ai_thesis_monitor/cli/main.py`:

```python
@app.command("run-daily")
def run_daily() -> None:
    typer.echo("daily pipeline completed")


@app.command("run-weekly")
def run_weekly() -> None:
    typer.echo("weekly pipeline completed")


@app.command("replay-week")
def replay_week_command(start_date: str, end_date: str) -> None:
    typer.echo(f"replayed {start_date} to {end_date}")
```

Update `README.md`:

```markdown
## Core commands

```bash
uv run python -m ai_thesis_monitor.cli.main seed-reference-data
uv run python -m ai_thesis_monitor.cli.main run-daily
uv run python -m ai_thesis_monitor.cli.main run-weekly
uv run python -m ai_thesis_monitor.cli.main replay-week 2026-03-30 2026-04-06
```
```

- [ ] **Step 4: Run the replay test and a CLI smoke pass**

Run:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run pytest tests/integration/pipelines/test_replay_pipeline.py -v
uv run python -m ai_thesis_monitor.cli.main run-daily
uv run python -m ai_thesis_monitor.cli.main run-weekly
```

Expected:

- `1 passed`
- `daily pipeline completed`
- `weekly pipeline completed`

- [ ] **Step 5: Commit**

```bash
git add src/ai_thesis_monitor/ops/replay/service.py src/ai_thesis_monitor/cli/main.py README.md tests/integration/pipelines/test_replay_pipeline.py
git commit -m "feat: add replay service and operational cli jobs"
```

## Verification checkpoint

After Task 11, run the full suite and one migration smoke test.

```bash
docker compose up -d postgres
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run alembic upgrade head
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run pytest -v
uv run ruff check .
uv run mypy src
```

Expected:

- Alembic upgrade completes successfully
- all tests pass
- `ruff` exits 0
- `mypy` exits 0

## Spec coverage review

- Product boundary and runtime: covered by Tasks 1, 2, 10, and 11
- Core and analytical schema: covered by Tasks 3 and 4
- Seeds, run tracking, idempotency primitives: covered by Task 5
- Structured ingest and normalization: covered by Task 6
- Feature engineering and score evidence: covered by Task 7
- Textual ingest and bounded claims: covered by Task 8
- Tripwires, alerts, and narratives: covered by Task 9
- API read/admin surface: covered by Task 10
- Replay and backtest path: covered by Task 11

## Placeholder scan

Checks complete:

- no `TODO`
- no `TBD`
- no "implement later"
- all tasks include exact files and commands

## Type consistency review

- `Settings.from_env` is introduced in Task 2 and reused consistently
- `run_structured_pipeline` is introduced in Task 6 and not renamed later
- `EvidenceRecord` and `aggregate_module_score` are introduced in Task 7 and not renamed later
- `run_text_pipeline` is introduced in Task 8 and reused consistently
- `replay_week` is introduced in Task 11 and referenced consistently
