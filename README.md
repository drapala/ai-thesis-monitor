# AI Thesis Monitor

## Executive Summary

Every week, the AI economy seems to tell two stories at once. In one, productivity is finally breaking loose: models improve, companies ship agents, costs fall, and more work gets done with less friction. In the other, the same signals look more ominous: hiring softens, white-collar tasks get cheaper, and what looks like efficiency at the firm level starts to threaten labor income, demand, and eventually credit. Both stories sound plausible. Most commentary chooses one too early.

`ai-thesis-monitor` exists to sit in that gap. It is a headless system for tracking two competing stories about AI in the US economy and forcing them to compete on observable evidence rather than mood. One story says AI behaves mostly like a messy but valuable productivity tool, slowed by institutions, integration costs, regulation, and the stubborn fact that organizations do not change overnight. The other says the pace is finally fast enough to matter where macro pain actually lives: white-collar labor, household income, demand, and eventually housing and credit.

The project does not try to predict "the future of AI" in the abstract. It asks a narrower and more useful question: which thesis is gaining strength now, through which causal channel, and because of what new evidence? To answer that, it ingests public macro series, labor signals, corporate text, and financial stress indicators, turns them into auditable evidence, and scores six causal modules instead of collapsing everything into one opaque number.

The result is closer to a weekly macro notebook than a dashboard. It records what changed, what merely got louder, what crossed from noise into regime, and what still has not been confirmed.

```text
How to read a week
------------------
public data + public text
          |
          v
   evidence by module
          |
          +--> citadel strength
          +--> citrini strength
          |
          v
 tripwires, alerts, weekly narrative
```

```text
Example weekly snapshot
-----------------------
Leader        citadel
Shift         productivity improved; labor weakened but not broadly enough to confirm regime change
Unconfirmed   no decisive spillover yet into demand, credit, or housing
```

This is not a passive dashboard project. The goal is to answer, repeatedly and explicitly:

1. Which thesis is gaining strength now?
2. In which causal module is that happening?
3. Is the move noise or regime?
4. Which evidence changed the system's belief?

## The Two Theses

- `citadel`: AI adoption grows, but institutional friction, integration cost, regulation, and human complementarity limit near-term macro damage.
- `citrini`: AI adoption grows fast enough to compress white-collar labor demand and income, weaken demand, erode intermediation rents, and eventually leak into credit and housing stress.

The system keeps both theses alive in parallel. It does not collapse the world into one opaque score.

## What It Analyzes

The V1 system evaluates six causal modules:

| Module | What it asks | Example signals |
| --- | --- | --- |
| `diffusion` | Is AI spreading fast enough to matter economically? | adoption rates, rollout intensity, hours saved, India IT AI revenue share |
| `productivity` | Is AI increasing output per worker or reducing hours per unit of output? | labor productivity, revenue per employee, India IT revenue/headcount, utilization rate |
| `labor` | Is productivity showing up as complement or substitution? | exposed job postings, layoffs, unemployment, India IT Big-4 headcount trend |
| `demand` | Is labor compression leaking into consumption? | discretionary spending, travel, restaurant spend, savings |
| `intermediation` | Are friction-based or SaaS-like business models losing pricing power? | renewal discounts, build-vs-buy mentions, take-rate pressure |
| `credit_housing` | Is the shock spreading into household balance sheets and housing? | delinquencies, HELOC draws, revolving balances, home prices |

### India IT proxy

TCS, Infosys, Wipro, and HCL collectively employ ~1.4 million white-collar workers and run AI delivery at enterprise scale for global clients. Their quarterly earnings reports are a high-frequency proxy for three modules simultaneously:

- **labor**: Big-4 combined headcount YoY captures whether global white-collar IT demand is expanding or contracting under AI pressure.
- **productivity**: TCS revenue per employee YoY and Wipro billable utilization rate measure whether the same headcount is producing more output — the citadel signal — or whether output is flat while headcount falls.
- **diffusion**: TCS annualized AI revenue as a share of total revenue (7.5% in Q4 FY26, up from ~4% in FY25) measures enterprise-scale AI adoption speed independently of any US survey data.

This proxy is particularly useful because India IT earnings are published quarterly with consistent methodology, cover both the supply side (what AI can do in delivery) and the demand side (what clients are buying), and are insulated from US survey self-reporting bias.

Data is seeded manually from press releases via `seed-india-it-data`. Quality scores on approximated intermediate quarters are set to 0.70 to reflect lower confidence.

V1 is intentionally narrow:

- `US-only` scope for macro signals; India IT used as a global proxy, not a domestic indicator
- public data only
- headless only
- no dashboard
- structured plus textual evidence from day 1

## How Analysis Works

The system turns external observations into auditable analytical outputs through a fixed pipeline:

1. `ingest`: fetch public structured series and public text sources into raw landing tables.
2. `parse`: normalize structured payloads into canonical metric points.
3. `extract claims`: convert relevant text into bounded, reviewable claims.
4. `build features`: derive trends, acceleration, baseline deviation, and other scoring inputs.
5. `score`: accumulate evidence separately for `citadel` and `citrini` by module.
6. `detect tripwires`: detect discrete regime-relevant events that deserve escalation.
7. `build narrative`: summarize what changed, where it changed, and what remains unconfirmed.

Three design rules matter:

- Every score must be traceable back to explicit evidence rows in Postgres.
- Text is assistive but bounded. Claims can influence a module, but they do not act as an unconstrained final judge.
- Tripwires are separate from routine scoring. They represent event-like jumps in belief, not ordinary weekly drift.

## What the System Produces

The repo persists five main analytical outputs:

- `score_evidence`: the metric- and claim-level contributions behind a weekly score
- `module_scores`: weekly dual scores for `citadel` and `citrini`, plus confidence and regime
- `tripwire_events`: discrete high-importance events such as persistent deterioration or critical claims
- `alerts`: the operational notification surface generated from tripwires
- `narrative_snapshots`: a human-readable weekly summary of the current analytical state

The intended weekly output is not just a number. It is an explainable snapshot of which thesis leads, why it leads, and what still has not been confirmed.

## Runtime Model

The repository is organized around five surfaces:

- `api`: FastAPI read and admin routes
- `cli`: explicit job entrypoints
- `domain`: pure scoring, tripwire, and narrative logic
- `ingestion`: adapters, parsers, and pipelines for structured and textual evidence
- `db` and `ops`: persistence, seeds, run tracking, and replay controls

Postgres is the source of truth. The system is designed for deterministic jobs, explicit run state, replay, and recomputation. V1 intentionally avoids queues, brokers, vector databases, and heavyweight orchestration.

## API Surface

The current FastAPI app exposes:

- `GET /health`
- `GET /scores/latest`
- `GET /alerts`
- `GET /narratives/latest`
- `GET /reviews/claims`
- `POST /reviews/claims/{claim_id}`
- `POST /admin/jobs/{job_name}`

The API is read-heavy and administrative. Analytical logic lives in domain and pipeline code, not in route handlers.

## Local Setup

1. Start Postgres: `docker compose up -d postgres`
2. Sync dependencies: `uv sync --extra dev`
3. Apply migrations:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run alembic upgrade head
```

4. Seed reference data and India IT historical data:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run python -m ai_thesis_monitor.cli.main seed-reference-data
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run python -m ai_thesis_monitor.cli.main seed-india-it-data
```

5. Run the test suite if you want a clean local verification pass:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run pytest -v
uv run ruff check .
uv run mypy src
```

6. Start the API if you want to inspect the read/admin surface locally:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run uvicorn ai_thesis_monitor.api.app:create_app --factory --reload
```

Postgres 16 is provided by `compose.yaml` and is exposed locally on port `54321`.

## CLI and Operational Commands

Print the installed version:

```bash
uv run ai-thesis-monitor version
```

Seed reference metadata and India IT historical data points:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run python -m ai_thesis_monitor.cli.main seed-reference-data
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run python -m ai_thesis_monitor.cli.main seed-india-it-data
```

`seed-india-it-data` is idempotent. Re-run after each quarterly earnings season to add the latest data point. Data lives in `src/ai_thesis_monitor/db/seeds/india_it_data.py`.

Reserved daily and weekly job entrypoints:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run python -m ai_thesis_monitor.cli.main run-daily
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run python -m ai_thesis_monitor.cli.main run-weekly
```

Replay a weekly window and rematerialize weekly outputs:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:54321/ai_thesis_monitor uv run python -m ai_thesis_monitor.cli.main replay-week 2026-03-30 2026-04-06
```

`replay-week` is the deterministic operational path that exercises weekly materialization against persisted evidence for a specific window.

## Repository Shape

```text
ai-thesis-monitor/
  alembic/
  docs/
  src/ai_thesis_monitor/
    api/
    app/
    cli/
    db/
    domain/
    ingestion/
    ops/
  tests/
```

The main architectural rule is separation of concerns:

- domain code should be understandable without reading transport or ORM code
- ingestion code should convert external material into internal artifacts
- persistence code should store and retrieve state, not decide analytical outcomes

## Current Evidence State

As of 2026-04-16, three modules have live data:

| Module | Regime | Lead signal |
| --- | --- | --- |
| `productivity` | **strong_citadel** | TCS revenue/employee +9% YoY; Wipro utilization +3.4σ above baseline; BLS +2.5% |
| `diffusion` | neutral | TCS AI revenue 7.5% of total — both theses agree adoption is growing |
| `labor` | leaning_citrini | Big-4 headcount -1.1% YoY; 25 text claims (Block, Meta, Pinterest AI layoffs) pending review |

The `demand`, `intermediation`, and `credit_housing` modules have metric definitions but no live data yet.

## MVP Boundaries

The current V1 contract is:

- public sources only
- US-only scope for macro indicators; India IT used as global proxy
- headless execution
- no end-user dashboard
- no end-to-end black-box scoring
- lightweight human review for important textual evidence

If you want the deeper design rationale, read [`docs/superpowers/specs/2026-04-13-ai-thesis-monitor-v1-design.md`](docs/superpowers/specs/2026-04-13-ai-thesis-monitor-v1-design.md).
