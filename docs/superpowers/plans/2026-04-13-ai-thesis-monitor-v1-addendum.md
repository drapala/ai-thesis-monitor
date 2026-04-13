# AI Thesis Monitor V1 Addendum Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the remaining V1 placeholders so weekly/replay runs materialize persisted outputs and the FastAPI surface reads and mutates the real database state.

**Architecture:** Keep the existing headless runtime and current persistence models. Move the weekly pipeline from an in-memory counter to the actual materialization boundary: it will read persisted `NormalizedMetric` and `Claim` rows, derive score evidence for modules that have live data, persist `ScoreEvidence`, `ModuleScore`, `TripwireEvent`, `Alert`, and `NarrativeSnapshot`, and use an explicit `score_date` instead of a hard-coded anchor. The API routes will stop returning stubs and instead use a shared request-scoped SQLAlchemy session dependency to read the latest rows and persist review/admin actions.

**Tech Stack:** Python 3.12, SQLAlchemy 2.x, FastAPI, Typer, pytest, Postgres 16

---

## Scope split

This addendum closes the three remaining gaps discovered in final review:

1. weekly/replay outputs are not written to the database
2. API routes are stubbed instead of backed by persistence
3. weekly tripwire dating is anchored to a hard-coded date

The smallest clean cut is:

1. materialize weekly state from the database
2. wire replay to that materializer
3. replace read/review/admin API placeholders with database-backed behavior

## File map

### Weekly materialization

- Modify: `src/ai_thesis_monitor/ingestion/pipelines/weekly.py` — replace hard-coded counter logic with DB-backed weekly materialization using explicit `score_date`
- Modify: `src/ai_thesis_monitor/ops/replay/service.py` — call the weekly materializer with `score_date=date.fromisoformat(end_date)` and remove hard-coded module histories
- Modify: `tests/unit/ingestion/test_weekly_pipeline.py` — assert persisted `ModuleScore` / `ScoreEvidence` / `TripwireEvent` / `Alert` / `NarrativeSnapshot`
- Modify: `tests/integration/pipelines/test_replay_pipeline.py` — assert replay writes weekly outputs for the replay window instead of only `PipelineRun`

### API persistence

- Create: `src/ai_thesis_monitor/api/deps.py` — request-scoped DB session dependency using `app.state.session_factory`
- Modify: `src/ai_thesis_monitor/api/app.py` — attach a reusable `session_factory` to app state
- Modify: `src/ai_thesis_monitor/api/routes/scores.py` — return latest persisted module scores
- Modify: `src/ai_thesis_monitor/api/routes/alerts.py` — return persisted alerts
- Modify: `src/ai_thesis_monitor/api/routes/narratives.py` — return the latest narrative snapshot
- Modify: `src/ai_thesis_monitor/api/routes/reviews.py` — list pending claim reviews and persist `review_status` updates
- Modify: `src/ai_thesis_monitor/api/routes/admin.py` — persist accepted admin-triggered runs instead of echoing input
- Modify: `tests/integration/api/test_read_routes.py` — seed DB rows and assert real read/write behavior

## Task 12: Materialize weekly scores, tripwires, alerts, and narratives

**Files:**
- Modify: `src/ai_thesis_monitor/ingestion/pipelines/weekly.py`
- Modify: `src/ai_thesis_monitor/ops/replay/service.py`
- Modify: `tests/unit/ingestion/test_weekly_pipeline.py`
- Modify: `tests/integration/pipelines/test_replay_pipeline.py`

- [ ] **Step 1: Write the failing weekly-materialization test**

```python
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ai_thesis_monitor.db.models.analytics import (
    Alert,
    Claim,
    ModuleScore,
    NarrativeSnapshot,
    NormalizedMetric,
    ScoreEvidence,
    TripwireEvent,
)
from ai_thesis_monitor.db.models.core import MetricDefinition, RawObservation, Source
from ai_thesis_monitor.ingestion.pipelines.weekly import run_weekly_pipeline


def test_run_weekly_pipeline_persists_outputs_for_explicit_score_date(db_session: Session) -> None:
    db_session.execute(delete(Alert))
    db_session.execute(delete(TripwireEvent))
    db_session.execute(delete(ScoreEvidence))
    db_session.execute(delete(ModuleScore))
    db_session.execute(delete(Claim))
    db_session.execute(delete(NormalizedMetric))
    db_session.execute(delete(RawObservation))
    db_session.execute(delete(MetricDefinition))
    db_session.execute(delete(Source))
    db_session.commit()

    source = Source(
        source_key="fred",
        source_name="Federal Reserve Economic Data",
        source_type="structured_csv",
        base_url="https://fred.stlouisfed.org",
        config={"path": "/graph/fredgraph.csv"},
        reliability_score=0.95,
        active=True,
    )
    definition = MetricDefinition(
        metric_key="unemployment_rate_professional_services",
        module_key="labor",
        name="Unemployment professional services",
        description="Unemployment rate in professional services",
        frequency="monthly",
        unit="percent",
        lag_category="confirmatory",
        weight=Decimal("1.100"),
        expected_direction_citadel="down",
        expected_direction_citrini="up",
        primary_feature_key="level",
        signal_transform="higher_is_citrini",
        min_history_points=1,
        is_leading=False,
        config={"source_key": "fred", "series_id": "UNRATE"},
        is_active=True,
    )
    raw = RawObservation(
        source_id=1,
        external_id="fred-unrate",
        payload={"series_id": "UNRATE"},
        content_hash="fred-unrate-v1",
    )
    db_session.add_all([source, definition])
    db_session.flush()
    raw.source_id = source.id
    db_session.add(raw)
    db_session.flush()

    db_session.add(
        NormalizedMetric(
            metric_definition_id=definition.id,
            source_id=source.id,
            raw_observation_id=raw.id,
            observed_date=date(2026, 4, 1),
            value=Decimal("4.2"),
            quality_score=Decimal("0.900"),
        )
    )
    db_session.add_all(
        [
            ModuleScore(
                module_key="labor",
                score_date=date(2026, 3, 23),
                score_citadel=Decimal("0.200"),
                score_citrini=Decimal("0.600"),
                confidence=Decimal("0.600"),
                winning_thesis="citrini",
                regime="leaning_citrini",
                explanation="history-1",
            ),
            ModuleScore(
                module_key="labor",
                score_date=date(2026, 3, 30),
                score_citadel=Decimal("0.150"),
                score_citrini=Decimal("0.650"),
                confidence=Decimal("0.620"),
                winning_thesis="citrini",
                regime="leaning_citrini",
                explanation="history-2",
            ),
        ]
    )
    db_session.commit()

    result = run_weekly_pipeline(db_session, score_date=date(2026, 4, 6))

    assert result.module_scores_written == 1
    assert result.tripwires_written == 1
    assert result.alerts_written == 1
    assert result.narratives_written == 1

    current_score = db_session.scalar(
        select(ModuleScore).where(
            ModuleScore.module_key == "labor",
            ModuleScore.score_date == date(2026, 4, 6),
        )
    )
    tripwire = db_session.scalar(select(TripwireEvent))
    alert = db_session.scalar(select(Alert))
    snapshot = db_session.scalar(
        select(NarrativeSnapshot).where(NarrativeSnapshot.snapshot_date == date(2026, 4, 6))
    )
    evidence_rows = db_session.scalars(
        select(ScoreEvidence).where(
            ScoreEvidence.module_key == "labor",
            ScoreEvidence.score_date == date(2026, 4, 6),
        )
    ).all()

    assert current_score is not None
    assert current_score.regime in {"leaning_citrini", "strong_citrini"}
    assert tripwire is not None
    assert tripwire.event_date == date(2026, 4, 6)
    assert alert is not None
    assert snapshot is not None
    assert snapshot.snapshot_date == date(2026, 4, 6)
    assert evidence_rows
```

- [ ] **Step 2: Run the weekly-materialization test to verify failure**

Run:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run pytest tests/unit/ingestion/test_weekly_pipeline.py::test_run_weekly_pipeline_persists_outputs_for_explicit_score_date -v
```

Expected: FAIL because `run_weekly_pipeline` does not accept a session/score date and does not persist any analytics rows

- [ ] **Step 3: Implement DB-backed weekly materialization**

`src/ai_thesis_monitor/ingestion/pipelines/weekly.py`

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ai_thesis_monitor.db.models.analytics import (
    Alert,
    Claim,
    ModuleScore,
    NarrativeSnapshot,
    NormalizedMetric,
    ScoreEvidence,
    TripwireEvent,
)
from ai_thesis_monitor.db.models.core import MetricDefinition, Source
from ai_thesis_monitor.domain.narratives.build import build_weekly_summary
from ai_thesis_monitor.domain.scoring.aggregation import aggregate_module_score
from ai_thesis_monitor.domain.scoring.evidence import EvidenceRecord
from ai_thesis_monitor.domain.tripwires.detect import detect_tripwires


@dataclass(frozen=True)
class WeeklyPipelineResult:
    module_scores_written: int
    tripwires_written: int
    alerts_written: int
    narratives_written: int


def run_weekly_pipeline(session: Session, *, score_date: date) -> WeeklyPipelineResult:
    evidence_by_module = _collect_evidence(session, score_date=score_date)
    session.execute(delete(ScoreEvidence).where(ScoreEvidence.score_date == score_date))
    session.execute(delete(Alert).where(Alert.alert_key.like(f"{score_date.isoformat()}:%")))
    session.execute(delete(TripwireEvent).where(TripwireEvent.event_date == score_date))
    session.execute(delete(ModuleScore).where(ModuleScore.score_date == score_date))
    session.execute(delete(NarrativeSnapshot).where(NarrativeSnapshot.snapshot_date == score_date))

    persisted_modules: list[ModuleScore] = []
    persisted_tripwires = 0
    persisted_alerts = 0

    for module_key, evidence_rows in evidence_by_module.items():
        if not evidence_rows:
            continue

        for evidence in evidence_rows:
            session.add(
                ScoreEvidence(
                    module_key=module_key,
                    score_date=score_date,
                    evidence_type=evidence.evidence_type,
                    bucket_key=evidence.bucket_key,
                    direction=evidence.direction,
                    strength=evidence.strength,
                    impact=evidence.impact,
                    weight=evidence.weight,
                    quality=evidence.quality,
                    contribution_citadel=evidence.contribution_citadel,
                    contribution_citrini=evidence.contribution_citrini,
                    explanation=evidence.explanation,
                    references=evidence.references,
                )
            )

        score = aggregate_module_score(module_key, evidence_rows)
        winning_thesis = "neutral"
        if score.score_citadel > score.score_citrini:
            winning_thesis = "citadel"
        elif score.score_citrini > score.score_citadel:
            winning_thesis = "citrini"

        persisted = ModuleScore(
            module_key=module_key,
            score_date=score_date,
            score_citadel=score.score_citadel,
            score_citrini=score.score_citrini,
            confidence=score.confidence,
            winning_thesis=winning_thesis,
            regime=score.regime,
            explanation=f"{len(evidence_rows)} evidence rows materialized for {module_key}",
        )
        session.add(persisted)
        persisted_modules.append(persisted)
        session.flush()

        prior_regimes = session.scalars(
            select(ModuleScore.regime)
            .where(
                ModuleScore.module_key == module_key,
                ModuleScore.score_date < score_date,
            )
            .order_by(ModuleScore.score_date.desc())
            .limit(2)
        ).all()
        score_dates = [
            score_date - timedelta(days=7 * offset)
            for offset in range(len(prior_regimes), 0, -1)
        ] + [score_date]
        regimes = list(reversed(prior_regimes)) + [score.regime]

        tripwires = detect_tripwires(
            module_key=module_key,
            score_dates=score_dates,
            regimes=regimes,
            critical_claims=[
                row.explanation
                for row in evidence_rows
                if row.evidence_type == "claim" and row.direction == "citrini"
            ],
        )
        for tripwire in tripwires:
            session.add(
                TripwireEvent(
                    module_key=module_key,
                    tripwire_key=tripwire.tripwire_key,
                    title=tripwire.tripwire_key.replace("_", " ").title(),
                    description=f"{module_key} triggered {tripwire.tripwire_key}",
                    direction=tripwire.direction,
                    severity=tripwire.severity,
                    trigger_type=tripwire.trigger_type,
                    event_date=tripwire.event_date,
                    valid_until=tripwire.valid_until,
                    decay_factor=Decimal(str(tripwire.decay_factor)),
                    evidence_refs={"module_key": module_key, "score_date": score_date.isoformat()},
                    review_status="not_required",
                )
            )
            session.add(
                Alert(
                    alert_key=f"{score_date.isoformat()}:{tripwire.tripwire_key}",
                    module_key=module_key,
                    severity=tripwire.severity,
                    title=tripwire.tripwire_key.replace("_", " ").title(),
                    message=f"{module_key} changed regime to {score.regime}",
                    status="open",
                )
            )
            persisted_tripwires += 1
            persisted_alerts += 1

    module_regimes = {row.module_key: row.regime for row in persisted_modules}
    summary = build_weekly_summary(
        overall_winner=_overall_winner(persisted_modules),
        module_regimes=module_regimes,
        new_evidence=[row.explanation for rows in evidence_by_module.values() for row in rows[:2]],
        open_questions=["coverage is limited to modules with live MVP evidence"],
    )
    session.add(
        NarrativeSnapshot(
            snapshot_date=score_date,
            overall_winner=_overall_winner(persisted_modules),
            confidence=max((row.confidence for row in persisted_modules), default=Decimal("0.500")),
            summary=summary,
            module_breakdown=module_regimes,
            supporting_evidence={
                module_key: [row.explanation for row in rows]
                for module_key, rows in evidence_by_module.items()
            },
        )
    )
    session.commit()
    return WeeklyPipelineResult(
        module_scores_written=len(persisted_modules),
        tripwires_written=persisted_tripwires,
        alerts_written=persisted_alerts,
        narratives_written=1,
    )
```

`src/ai_thesis_monitor/ops/replay/service.py`

```python
from datetime import date

from ai_thesis_monitor.ingestion.pipelines.weekly import run_weekly_pipeline


def _replay_week_transaction(
    session: Session,
    *,
    start_date: str,
    end_date: str,
) -> ReplayResult:
    ...
    weekly_result = run_weekly_pipeline(
        session,
        score_date=date.fromisoformat(end_date),
    )
    ...
```

- [ ] **Step 4: Extend the replay integration test to assert persisted weekly outputs**

```python
def test_replay_week_records_materialized_outputs(cli_runner, db_session) -> None:
    result = cli_runner.invoke(app, ["replay-week", REPLAY_START, REPLAY_END])
    assert result.exit_code == 0

    snapshot = db_session.scalar(
        select(NarrativeSnapshot).where(NarrativeSnapshot.snapshot_date == date(2026, 4, 6))
    )
    assert snapshot is not None

    scores = db_session.scalars(
        select(ModuleScore).where(ModuleScore.score_date == date(2026, 4, 6))
    ).all()
    assert scores
```

- [ ] **Step 5: Run the weekly/replay tests**

Run:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run pytest tests/unit/ingestion/test_weekly_pipeline.py tests/integration/pipelines/test_replay_pipeline.py -v
```

Expected: PASS with all weekly and replay tests green

- [ ] **Step 6: Commit**

```bash
git add src/ai_thesis_monitor/ingestion/pipelines/weekly.py src/ai_thesis_monitor/ops/replay/service.py tests/unit/ingestion/test_weekly_pipeline.py tests/integration/pipelines/test_replay_pipeline.py
git commit -m "feat: persist weekly materialized outputs"
```

## Task 13: Replace API placeholders with DB-backed reads, reviews, and admin triggers

**Files:**
- Create: `src/ai_thesis_monitor/api/deps.py`
- Modify: `src/ai_thesis_monitor/api/app.py`
- Modify: `src/ai_thesis_monitor/api/routes/scores.py`
- Modify: `src/ai_thesis_monitor/api/routes/alerts.py`
- Modify: `src/ai_thesis_monitor/api/routes/narratives.py`
- Modify: `src/ai_thesis_monitor/api/routes/reviews.py`
- Modify: `src/ai_thesis_monitor/api/routes/admin.py`
- Modify: `tests/integration/api/test_read_routes.py`

- [ ] **Step 1: Write the failing API integration test for persisted reads/writes**

```python
from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import delete

from ai_thesis_monitor.api.app import create_app
from ai_thesis_monitor.db.models.analytics import Alert, Claim, ModuleScore, NarrativeSnapshot
from ai_thesis_monitor.db.models.core import Document, DocumentChunk, PipelineRun, RawObservation, Source


def test_read_routes_return_persisted_state(db_session) -> None:
    db_session.execute(delete(PipelineRun))
    db_session.execute(delete(Alert))
    db_session.execute(delete(ModuleScore))
    db_session.execute(delete(NarrativeSnapshot))
    db_session.execute(delete(Claim))
    db_session.execute(delete(DocumentChunk))
    db_session.execute(delete(Document))
    db_session.execute(delete(RawObservation))
    db_session.execute(delete(Source))
    db_session.commit()

    source = Source(
        source_key="rss_corporate_ir",
        source_name="Corporate IR RSS",
        source_type="rss",
        base_url="https://rss.example.test/corporate-ir.xml",
        config={"kind": "corporate"},
        reliability_score=0.82,
        active=True,
    )
    db_session.add(source)
    db_session.flush()
    raw = RawObservation(
        source_id=source.id,
        external_id="claim-1",
        payload={"claim": 1},
        content_hash="claim-1",
    )
    db_session.add(raw)
    db_session.flush()
    document = Document(
        source_id=source.id,
        raw_observation_id=raw.id,
        title="ServiceNow reduces workforce while increasing AI investment",
        url="https://example.test/claim-1",
        body_text="ServiceNow said it would reduce workforce and invest more in AI efficiency programs.",
    )
    db_session.add(document)
    db_session.flush()
    chunk = DocumentChunk(document_id=document.id, chunk_index=0, chunk_text=document.body_text, chunk_hash="chunk-1")
    db_session.add(chunk)
    db_session.add(
        Claim(
            source_id=source.id,
            raw_observation_id=raw.id,
            document_id=document.id,
            chunk_id=chunk.id,
            module_key="labor",
            claim_type="headcount_reduction_ai_efficiency",
            entity="ServiceNow",
            claim_text=document.title,
            evidence_direction="citrini",
            strength=Decimal("0.820"),
            confidence=Decimal("0.760"),
            dedupe_key="claim-1",
            review_status="pending_review",
        )
    )
    db_session.add(
        ModuleScore(
            module_key="labor",
            score_date=date(2026, 4, 6),
            score_citadel=Decimal("0.100"),
            score_citrini=Decimal("0.900"),
            confidence=Decimal("0.720"),
            winning_thesis="citrini",
            regime="strong_citrini",
            explanation="labor deteriorated",
        )
    )
    db_session.add(
        Alert(
            alert_key="2026-04-06:labor_persistent_deterioration_3w",
            module_key="labor",
            severity="warning",
            title="Labor Persistent Deterioration 3W",
            message="labor changed regime to strong_citrini",
            status="open",
        )
    )
    db_session.add(
        NarrativeSnapshot(
            snapshot_date=date(2026, 4, 6),
            overall_winner="citrini",
            confidence=Decimal("0.720"),
            summary="citrini leads this week",
            module_breakdown={"labor": "strong_citrini"},
            supporting_evidence={"labor": ["labor deteriorated"]},
        )
    )
    db_session.commit()

    client = TestClient(create_app())

    assert client.get("/scores/latest").json()["items"][0]["module_key"] == "labor"
    assert client.get("/alerts").json()["items"][0]["alert_key"] == "2026-04-06:labor_persistent_deterioration_3w"
    assert client.get("/narratives/latest").json()["snapshot"]["overall_winner"] == "citrini"
    assert client.get("/reviews/claims").json()["items"][0]["review_status"] == "pending_review"

    review_resp = client.post("/reviews/claims/1", params={"status": "approved"})
    assert review_resp.status_code == 200
    assert review_resp.json()["status"] == "approved"

    admin_resp = client.post("/admin/jobs/weekly")
    assert admin_resp.status_code == 200
    assert admin_resp.json()["status"] == "accepted"

    db_session.expire_all()
    assert db_session.get(Claim, 1).review_status == "approved"
    assert db_session.scalar(select(PipelineRun.run_type).order_by(PipelineRun.id.desc())) == "weekly"
```

- [ ] **Step 2: Run the API integration test to verify failure**

Run:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run pytest tests/integration/api/test_read_routes.py::test_read_routes_return_persisted_state -v
```

Expected: FAIL because the routes still return placeholders and do not persist mutations

- [ ] **Step 3: Implement request-scoped DB dependencies and real route behavior**

`src/ai_thesis_monitor/api/deps.py`

```python
from __future__ import annotations

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy.orm import Session


def get_db_session(request: Request) -> Iterator[Session]:
    session_factory = request.app.state.session_factory
    with session_factory() as session:
        yield session
```

`src/ai_thesis_monitor/api/app.py`

```python
from ai_thesis_monitor.app.db import build_session_factory


def create_app() -> FastAPI:
    configure_logging()
    settings = Settings.from_env(os.environ)
    app = FastAPI(title=settings.app_name)
    app.state.settings = settings
    app.state.session_factory = build_session_factory(settings)
    ...
    return app
```

`src/ai_thesis_monitor/api/routes/scores.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_thesis_monitor.api.deps import get_db_session
from ai_thesis_monitor.db.models.analytics import ModuleScore

router = APIRouter(prefix="/scores", tags=["scores"])


@router.get("/latest")
def read_latest_scores(session: Session = Depends(get_db_session)) -> dict[str, list[dict]]:
    latest_score_date = session.scalar(select(ModuleScore.score_date).order_by(ModuleScore.score_date.desc()))
    if latest_score_date is None:
        return {"items": []}
    rows = session.scalars(
        select(ModuleScore)
        .where(ModuleScore.score_date == latest_score_date)
        .order_by(ModuleScore.module_key)
    ).all()
    return {
        "items": [
            {
                "module_key": row.module_key,
                "score_date": row.score_date.isoformat(),
                "score_citadel": str(row.score_citadel),
                "score_citrini": str(row.score_citrini),
                "confidence": str(row.confidence),
                "winning_thesis": row.winning_thesis,
                "regime": row.regime,
                "explanation": row.explanation,
            }
            for row in rows
        ]
    }
```

Apply the same pattern to:

- `alerts.py`: read `Alert` rows ordered by `triggered_at DESC`
- `narratives.py`: read latest `NarrativeSnapshot`
- `reviews.py`: list `Claim.review_status == "pending_review"` and update a specific `Claim.review_status`
- `admin.py`: insert `PipelineRun(run_type=job_name, status="accepted", triggered_by="api", inputs={}, outputs_summary={})`

- [ ] **Step 4: Run the API integration test**

Run:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run pytest tests/integration/api/test_read_routes.py -v
```

Expected: PASS with persisted API reads and writes

- [ ] **Step 5: Commit**

```bash
git add src/ai_thesis_monitor/api/deps.py src/ai_thesis_monitor/api/app.py src/ai_thesis_monitor/api/routes/scores.py src/ai_thesis_monitor/api/routes/alerts.py src/ai_thesis_monitor/api/routes/narratives.py src/ai_thesis_monitor/api/routes/reviews.py src/ai_thesis_monitor/api/routes/admin.py tests/integration/api/test_read_routes.py
git commit -m "feat: back api routes with persisted state"
```

## Verification checkpoint

After the addendum tasks, rerun the full branch checkpoint.

```bash
docker compose up -d postgres
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run alembic upgrade head
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run pytest -v
uv run ruff check .
uv run mypy src
```

Expected:

- weekly/replay tests show persisted outputs instead of placeholder counters only
- API integration tests read persisted scores/alerts/narratives and mutate claim review/admin runs
- all tests pass
- `ruff` exits 0
- `mypy` exits 0
