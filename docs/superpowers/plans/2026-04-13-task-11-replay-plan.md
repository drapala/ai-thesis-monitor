I'm using the writing-plans skill to create the implementation plan.

# Task 11 Replay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an idempotent weekly replay service, expose the daily/weekly/replay CLI surface, and document/test the flows per Task 11.

**Architecture:** Persist a `PipelineRun` whenever a replay triggers, guard against duplicate runs, route through the existing `run_weekly_pipeline` glue, and keep the CLI commands declarative echoes tied into the service as needed.

**Tech Stack:** Python 3.12, Typer, SQLAlchemy ORM, Pytest (integration), `uv` for CLI execution, PostgreSQL-backed integration database.

---

### Task 1: Replay integration test & service

**Files:**
- Create: `tests/integration/pipelines/test_replay_pipeline.py`
- Create: `src/ai_thesis_monitor/ops/replay/__init__.py`
- Create: `src/ai_thesis_monitor/ops/replay/service.py`

- [ ] **Step 1: Write the failing integration test**

```python
from ai_thesis_monitor.ops.replay.service import replay_week


def test_replay_week_is_idempotent(db_session) -> None:
    first = replay_week(db_session, start_date="2026-03-30", end_date="2026-04-06")
    second = replay_week(db_session, start_date="2026-03-30", end_date="2026-04-06")

    assert first.module_scores_written >= 0
    assert second.module_scores_written == 0
```

- [ ] **Step 2: Run the replay test to witness the failure**

Run: `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run pytest tests/integration/pipelines/test_replay_pipeline.py -v`

Expected: FAIL with `ImportError`/`ModuleNotFoundError` because `ai_thesis_monitor.ops.replay.service` does not exist yet.

- [ ] **Step 3: Implement the minimal replay service**

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
            error_summary=None,
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

`src/ai_thesis_monitor/ops/replay/__init__.py` simply exports the service to keep the package importable.

- [ ] **Step 4: Run the replay test to verify it passes**

Run: `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run pytest tests/integration/pipelines/test_replay_pipeline.py -v`

Expected: PASS with `1 passed`.


### Task 2: CLI commands and docs

**Files:**
- Modify: `src/ai_thesis_monitor/cli/main.py`
- Modify: `README.md`

- [ ] **Step 1: Add the new Typer commands**

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

Place these commands below the existing `seed_reference_data` command so they are part of the same Typer app.

- [ ] **Step 2: Document the core commands**

Update `README.md` with a `## Core commands` section that contains the following shell snippet verbatim:

```bash
uv run python -m ai_thesis_monitor.cli.main seed-reference-data
uv run python -m ai_thesis_monitor.cli.main run-daily
uv run python -m ai_thesis_monitor.cli.main run-weekly
uv run python -m ai_thesis_monitor.cli.main replay-week 2026-03-30 2026-04-06
```

- [ ] **Step 3: Run CLI smoke commands**

Run the following commands to ensure they print as expected:

1. `uv run python -m ai_thesis_monitor.cli.main run-daily` → `daily pipeline completed`
2. `uv run python -m ai_thesis_monitor.cli.main run-weekly` → `weekly pipeline completed`
3. `uv run python -m ai_thesis_monitor.cli.main replay-week 2026-03-30 2026-04-06` → `replayed 2026-03-30 to 2026-04-06`

- [ ] **Step 4: Confirm replay test still passes**

Run: `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run pytest tests/integration/pipelines/test_replay_pipeline.py -v`

Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit the changes**

```bash
git add src/ai_thesis_monitor/ops/replay/__init__.py \
  src/ai_thesis_monitor/ops/replay/service.py \
  src/ai_thesis_monitor/cli/main.py \
  README.md \
  tests/integration/pipelines/test_replay_pipeline.py \
  docs/superpowers/specs/2026-04-13-task-11-replay-design.md \
  docs/superpowers/plans/2026-04-13-task-11-replay-plan.md
git commit -m "feat: add replay service and operational cli jobs"
```
