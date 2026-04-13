# AI Thesis Monitor

Minimal runtime and CLI orchestrator for monitoring AI thesis deployments.

## Local setup

1. Start the local PostgreSQL service: `docker compose up -d postgres`
2. Sync dependencies: `uv sync --extra dev`
3. Run the CLI smoke test: `uv run pytest tests/unit/test_cli_smoke.py -v`

## CLI

Invoke the Typer CLI through `uv run ai-thesis-monitor version` to print the current
`0.1.0` release string.

## Core commands

Apply the database migrations/schema before running these commands:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run alembic upgrade head
```

```bash
uv run python -m ai_thesis_monitor.cli.main seed-reference-data
uv run python -m ai_thesis_monitor.cli.main run-daily
uv run python -m ai_thesis_monitor.cli.main run-weekly
uv run python -m ai_thesis_monitor.cli.main replay-week 2026-03-30 2026-04-06
```

## Database

Postgres 16 runs inside `docker compose` and is wired up on port `54321`.
