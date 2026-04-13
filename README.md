# AI Thesis Monitor

Minimal runtime and CLI orchestrator for monitoring AI thesis deployments.

## Local setup

1. Start the local PostgreSQL service: `docker compose up -d postgres`
2. Sync dependencies: `uv sync --extra dev`
3. Run the CLI smoke test: `uv run pytest tests/unit/test_cli_smoke.py -v`

## CLI

Invoke the Typer CLI through `uv run ai-thesis-monitor version` to print the current
`0.1.0` release string.

## Database

Postgres 16 runs inside `docker compose` and is wired up on port `54321`.
