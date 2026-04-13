# Task 11 Replay Design

**Date:** 2026-04-13

## Overview

Task 11 introduces the operational surface for replaying a weekly pipeline, running the daily/weekly jobs, and documenting those flows. The core acceptance criteria boil down to: (1) an idempotent `replay_week` service that records completed runs and routes through the existing weekly pipeline glue, (2) CLI commands that expose the daily, weekly, and replay entry points, and (3) documentation plus an integration test that demonstrates the replay path failing before the service exists.

## Constraints and Principles

* Follow the prescribed TDD cycle: write the failing integration test, observe the failure, implement the minimal service and CLI hooks, rerun the targeted test.
* Keep the implementation surface minimal (hard-coded module history example, simplest CLI echoes) unless the product owners request broader orchestration.
* Honor idempotency by checking for an existing `PipelineRun(run_type="replay_week", inputs={"start_date": …, "end_date": …})` before running the pipeline.
* The service should only depend on `PipelineRun` persistence plus `run_weekly_pipeline` from the ingestion layer; no new database tables or complicated job orchestration.

## Technical Design

### Replay Service

* Introduce `ReplayResult` as a frozen dataclass mirroring `WeeklyPipelineResult`.
* Implement `replay_week(session, *, start_date, end_date) -> ReplayResult` inside `ai_thesis_monitor.ops.replay.service`.
* Query `PipelineRun` for the matching replay inputs and return zeroed counts if found.
* When no previous run exists, insert a completed `PipelineRun` with `run_type="replay_week"`, `triggered_by="cli"`, `inputs={"start_date":…, "end_date":…}`, `outputs_summary={"mode":"replay"}`, and commit immediately.
* After persisting, call `run_weekly_pipeline` with the approved hard-coded module history (`{"labor": ["leaning_citrini", "strong_citrini"]}`) and empty critical claims, then map its `WeeklyPipelineResult` into `ReplayResult`.

### CLI Commands

* The Typer app in `ai_thesis_monitor.cli.main` gains three new commands:
  * `run-daily` – prints `daily pipeline completed`.
  * `run-weekly` – prints `weekly pipeline completed`.
  * `replay-week START END` – prints `replayed START to END`.
* These commands stay intentionally light and are currently limited to echoing strings while keeping the door open to future service calls.

### Testing & Documentation

* Create `tests/integration/pipelines/test_replay_pipeline.py` containing the approved idempotency test: two successive `replay_week` calls with the same dates and assertions that the first writes module scores (>=0) while the second reports zero.
* Source the database session via the existing `db_session` fixture and rely on the PostgreSQL-backed integration environment described in Task 11’s plan.
* Update `README.md` with the `Core commands` section listing the four CLI invocations under `uv run python -m ai_thesis_monitor.cli.main …`.

## Verification Steps

1. Run the new integration test (`tests/integration/pipelines/test_replay_pipeline.py`) before the service exists and confirm it fails as expected.
2. Implement the service, CLI commands, README update, and rerun the targeted test to confirm it passes.
3. (Later, after Task 11) run the broader verification sequence (docker compose up, alembic upgrade, full test suite, ruff, mypy).

## Next Actions

1. Once this design has your signoff, I will commit this spec (`docs/superpowers/specs/2026-04-13-task-11-replay-design.md`) and request your review on the file.
2. After you confirm the spec is correct, I will invoke the writing-plans workflow and start the failing test → implementation sequence outlined above.
