# AI Thesis Monitor V1 Design

Date: 2026-04-13
Status: Approved for implementation planning
Project: `ai-thesis-monitor`

## Summary

`ai-thesis-monitor` is a standalone, headless observability system for continuously testing two competing macro theses about AI diffusion and economic impact in the United States:

- `citadel`: AI accelerates, but institutional friction, integration cost, regulation, and human complementarity limit near-term macro damage.
- `citrini`: AI accelerates fast enough to compress white-collar labor demand and income, weaken discretionary demand, erode intermediation rents, and eventually leak into credit and housing stress.

The system is not a passive dashboard. It is a hypothesis-first evidence engine that ingests structured and textual public data, normalizes it into auditable evidence, scores each module weekly, detects tripwires, and produces explainable narrative snapshots.

V1 is intentionally narrow:

- standalone repository under `projects/ai-thesis-monitor`
- headless only
- US-only
- public data only
- structured and textual evidence from day 1
- Postgres as source of truth
- deterministic jobs with explicit run state
- no dashboard
- no queue, broker, Airflow, or Temporal

## Goals

V1 must answer four questions on a recurring basis:

1. Which thesis is gaining strength now?
2. In which causal module is that happening?
3. Is the move noise or regime?
4. Which concrete evidence changed the system's belief?

## Non-goals

V1 does not attempt to:

- predict "the future of AI" in a generic sense
- support multiple geographies
- run real-time streaming analytics
- perform end-to-end black-box inference
- depend on paid data vendors
- ship a UI or dashboard
- use social media exhaust as a primary signal source

## Design Principles

- Hypothesis-first: every metric, claim, and tripwire exists to test a causal link in the thesis map.
- Explainability-first: every score and alert must be traceable to explicit evidence records.
- Structured plus textual fusion: slow public time series and faster qualitative evidence both matter.
- Lead plus confirmatory signals: the system should use faster weak signals without letting them dominate.
- Tripwire over noise: discrete regime-relevant events matter more than isolated fluctuations.
- Human review where it matters: critical textual evidence and critical tripwires must support lightweight manual review.
- No end-to-end black box: LLMs may classify, extract, and summarize, but never serve as the final judge of thesis state.

## V1 Scope

### Causal modules

V1 covers six modules:

1. `diffusion`
2. `productivity`
3. `labor`
4. `demand`
5. `intermediation`
6. `credit_housing`

### Analytical scope

V1 targets:

- 20 to 25 active metrics
- 4 to 6 live connectors in the first operating cut
- weekly module scoring
- weekly narrative snapshots
- daily ingestion and feature refresh
- lightweight review of critical evidence

Metric definitions may be seeded more broadly, but only a smaller subset should be active in the first production cycle.

## Recommended architecture

The selected approach is `core operational first`.

This keeps Postgres at the center, exposes jobs as explicit commands, and treats textual evidence as bounded, auditable input instead of system-wide control logic. It avoids early orchestration complexity while preserving replayability and analytical rigor.

## Product boundary and runtime

V1 runs as a standalone repository with five surfaces:

- `api`: FastAPI endpoints for health, read access to scores, alerts, snapshots, and limited admin triggers
- `jobs`: explicit entrypoints for ingest, parse, feature building, scoring, tripwire detection, and narrative generation
- `db`: schema migrations, seeds, and persistence models
- `domain`: pure analytical logic for scoring, tripwires, explanations, and narratives
- `ops`: run tracking, replay support, idempotency, and operational troubleshooting

Operational constraints:

- Postgres is the source of truth
- scheduling is handled by cron or a simple local runner
- run state lives in the database
- the system must support recomputation from persisted state
- there is no broker, queue, vector database, or heavyweight workflow orchestrator in V1

Cadence:

- daily: ingestion, parsing, claim extraction, feature refresh
- weekly: score computation, tripwire detection, narrative snapshot generation, alerts

## Repository layout

The repository should start with this structure:

```text
ai-thesis-monitor/
  alembic/
  docs/
    superpowers/
      specs/
  src/ai_thesis_monitor/
    api/
      routes/
      schemas/
    app/
      settings.py
      logging.py
      db.py
    cli/
      main.py
    db/
      models/
      repositories/
      seeds/
    domain/
      claims/
      metrics/
      narratives/
      scoring/
      tripwires/
    ingestion/
      adapters/
      parsers/
      pipelines/
    ops/
      replay/
      runs/
  tests/
    fixtures/
    integration/
    unit/
  scripts/
  pyproject.toml
  README.md
```

Boundary rules:

- `domain/` does not depend on FastAPI, SQLAlchemy, or HTTP clients
- `db/` handles persistence only
- `ingestion/` converts external source material into internal artifacts
- `cli/` maps job entrypoints to application services
- `api/` is read-heavy and administrative, not a second execution path for business logic

## Data model

The schema is split into five layers.

### 1. Configuration

Reference tables seeded at startup:

- `sources`
- `metric_definitions`

`metric_definitions` must include enough metadata to evaluate and score a metric without hidden code paths. In addition to the initial fields, V1 should add:

- `primary_feature_key`
- `signal_transform`
- `min_history_points`
- `is_leading`

### 2. Operations

Operational audit tables:

- `pipeline_runs`
- `job_runs`

`pipeline_runs` represents a scheduled or manual execution window such as daily, weekly, or backfill. `job_runs` stores each concrete step and must include:

- `run_id`
- `job_name`
- `status`
- `started_at`
- `finished_at`
- `inputs`
- `outputs_summary`
- `error_summary`
- `cursor_in`
- `cursor_out`

These tables are mandatory for observability, replay, and troubleshooting in a headless system.

### 3. Landing and source material

Immutable or append-oriented source landing:

- `raw_observations`
- `documents`
- `document_chunks`

`raw_observations` stores canonical source payloads for both structured and textual ingestion. `documents` and `document_chunks` materialize textual source content into auditable units for extraction and review.

### 4. Normalized evidence inputs

Derived data that remains close to the original signal:

- `normalized_metrics`
- `metric_features`
- `claims`

`normalized_metrics` holds canonical metric points. `metric_features` stores derived values such as short-window trend, acceleration, rolling z-score, baseline deviation, and cross-confirmation flags. `claims` stores extracted textual evidence.

### 5. Analytical outputs

Inference and downstream outputs:

- `score_evidence`
- `module_scores`
- `tripwire_events`
- `alerts`
- `narrative_snapshots`

`score_evidence` is a first-class table, not implied logic. Every module score must be explainable via explicit supporting evidence rows.

## Required table behaviors

The initial schema provided for V1 remains directionally correct and should be extended with the following behaviors.

### Idempotency

- structured and textual ingestion uses `source_id + external_id` when `external_id` exists
- fallback deduplication uses `source_id + content_hash`
- `claims` deduplicate on `dedupe_key`
- `module_scores` are unique on `module_key + score_date`
- `narrative_snapshots` are unique on `snapshot_date`

### Normalized metric uniqueness

`normalized_metrics` must enforce semantic uniqueness on:

- `metric_definition_id`
- `source_id`
- `observed_date`
- `geo`
- `segment`

### Review state

`claims` and `tripwire_events` must carry `review_status` with:

- `not_required`
- `pending_review`
- `approved`
- `rejected`

This is the minimum manual review queue for critical evidence in a headless system.

## Job contracts

V1 uses explicit jobs rather than generic internal phases.

### `ingest-structured`

- reads active structured sources
- fetches payloads
- canonicalizes source data
- computes dedupe identifiers
- writes only to `raw_observations`

### `ingest-text`

- reads active textual sources
- fetches documents or feeds
- canonicalizes text payloads
- computes dedupe identifiers
- writes only to `raw_observations`

### `parse-structured`

- reads structured `raw_observations`
- maps payloads to canonical metrics
- upserts into `normalized_metrics`

### `extract-claims`

- reads textual `raw_observations`
- materializes `documents` and `document_chunks`
- classifies relevance and module
- extracts structured `claims`
- assigns review state where required

### `build-features`

- reads `normalized_metrics`
- computes rolling and windowed derived features
- upserts into `metric_features`

### `score`

- reads `metric_features` and eligible `claims`
- evaluates signals into evidence records
- writes `score_evidence`
- writes `module_scores`

### `detect-tripwires`

- reads recent features, claims, and module scores
- evaluates threshold, pattern, claim, and cross-signal triggers
- writes `tripwire_events`
- writes `alerts` when severity and confirmation rules are satisfied

### `build-narrative`

- reads `module_scores`, `score_evidence`, and `tripwire_events`
- renders bounded weekly narrative output
- writes `narrative_snapshots`

## Scoring model

V1 uses dual evidence accounting. The system never compresses all evidence into a single opaque scalar.

Each evaluated input becomes a `score_evidence` record with:

- `module_key`
- `score_date`
- `evidence_type`
- `direction`
- `strength`
- `impact`
- `weight`
- `quality`
- `contribution_citadel`
- `contribution_citrini`
- `explanation`
- `references`

Important distinction:

- `strength` describes how strong the signal is in its own terms
- `impact` describes how much that signal should matter for the module

This avoids mixing magnitude with module relevance.

### Aggregation

For each module and score date, the engine accumulates:

- `score_citadel`
- `score_citrini`
- `net_score`
- `confidence`
- `winning_thesis`
- `regime`

### Confidence

Confidence is an auditable function of:

- source quality
- signal independence
- coherence across evidence
- persistence through time

The formula does not need to be elegant in V1, but it must be stable, inspectable, and deterministic.

### Independence buckets

Signal independence must be operationalized, not hand-waved. V1 uses capped buckets such as:

- macro
- labor platforms
- corporate
- financial
- textual claims

No single bucket should dominate the full module score by volume alone.

### Textual contribution cap

Textual evidence is assistive but bounded. V1 must enforce a global cap on textual contribution per module score. Initial target:

- textual evidence contributes at most 30 to 40 percent of total module score

### Regimes

Supported module regimes:

- `strong_citadel`
- `leaning_citadel`
- `neutral`
- `leaning_citrini`
- `strong_citrini`
- `conflicted`

`conflicted` is used when high-quality evidence strongly supports both sides at once. This is analytically distinct from `neutral`.

### Regime gating

A strong regime may only be produced when:

- persistence exceeds a configured minimum number of consecutive scoring windows, or
- a critical reviewed tripwire explicitly overrides the persistence gate

This prevents one-off events from creating regime flip-flops.

## Tripwire engine

Tripwires are discrete, regime-relevant events with more update power than ordinary evidence rows.

V1 supports four tripwire types:

- `threshold`
- `pattern`
- `claim`
- `cross_signal`

Each tripwire includes:

- `tripwire_key`
- `module_key`
- `direction`
- `severity`
- `trigger_type`
- `evidence_refs`
- `review_status`
- `explanation`
- `valid_until`
- `decay_factor`

Tripwires do not replace scoring. They modify urgency, confidence, and alerting behavior. Their impact must decay over time rather than persisting forever.

## Textual evidence policy

This is a constitutional rule for V1:

- text may produce claims
- claims may influence scores
- claims may reinforce, anticipate, or contextualize structured evidence
- claims alone may not create `strong_citadel` or `strong_citrini`
- exception: a critical tripwire may escalate significance, but it still requires explicit review state and source traceability

Claims with `rejected` review status contribute nothing. Claims with `pending_review` may contribute only under reduced weight.

## Narrative generation

Narrative output is a render layer, not an inference layer.

The narrative engine reads only previously computed artifacts and produces a bounded weekly summary. It must not invent new evidence or conduct fresh reasoning outside the scored state.

Each weekly narrative must answer:

- which thesis leads now
- in which modules that lead is strongest
- what changed this week
- what remains unconfirmed
- which tripwires matter now

V1 narratives should be template-driven with ranked evidence insertion, not open-ended essay generation.

## Public source strategy

V1 uses public sources only. The first operating cut should focus on a disciplined core set rather than broad coverage.

### Structured source candidates

- BLS
- JOLTS
- CPS
- BLS productivity
- BEA consumption series
- NY Fed household credit indicators
- FRED as a public access layer for stable series
- Indeed Hiring Lab

### Textual source candidates

- public earnings-call transcripts where accessible
- investor relations press releases
- Fed blogs including Liberty Street
- Brookings and similar public institutional analysis
- selectively ingested high-quality macro and finance reporting

Restrictions:

- no wide social crawling
- no broad forum ingestion
- no paid vendor APIs in V1
- no source enters the active set without explicit definition and reliability scoring

## MVP metric discipline

V1 only works if the active metric and connector set stays narrow. The first cut must remain:

- narrow
- auditable
- recalibratable
- intentionally dry

The product fails if it becomes analytically baroque before the evidence model is stable.

## Validation strategy

V1 must prove technical integrity and analytical discipline before expanding coverage.

### Technical validation

- ingestion is idempotent
- retries and circuit breaking behave correctly per source
- parser output is deterministic for versioned fixtures
- metric, claim, and score upserts are stable
- replay of `job_runs` does not create semantic duplicates

### Analytical validation

- feature derivation is correct on known fixtures
- dual scoring is reproducible for fixed evidence inputs
- textual contribution cap is enforced
- bucket caps prevent false independence inflation
- strong regime gating blocks premature regime classification

### Product sanity checks

- every narrative references real evidence in the database
- every module score can be explained through `score_evidence`
- every tripwire points to inspectable source material
- rejected claims disappear from recomputed scores

### Historical backtest

V1 should be run over a short historical window, such as 6 to 12 months, not to claim predictive accuracy but to test:

- pipeline stability
- threshold sensitivity
- false tripwire frequency
- whether narratives track real changes without dramatizing noise

## Concrete stack

V1 should use:

- Python 3.12
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- psycopg
- Alembic
- httpx
- tenacity
- pybreaker
- Typer
- pytest
- ruff
- mypy
- Postgres 16

The project should not introduce Celery, Redis, SQLModel, Temporal, Airflow, or a vector database in the first implementation plan.

## Risks and controls

### Primary risk: analytical sprawl

Too many sources, claims, or metrics too early will produce a noisy system that feels rich but cannot be calibrated.

Control:

- limit live connectors
- limit active metrics
- require explicit review state for critical evidence
- prefer clean evidence traces over coverage breadth

### Primary technical risk: source brittleness

Public textual sources will break more often than structured APIs.

Control:

- isolate adapters
- keep parse and extract stages separate
- persist raw payloads
- record failure modes in `job_runs`

### Primary interpretive risk: textual overreach

Narrative volume can overpower structured signals if left unconstrained.

Control:

- textual contribution cap
- regime gating
- reviewed tripwire escalation only

## Implementation handoff

The next step is not coding yet. The next step is a written implementation plan that breaks this V1 into executable milestones, tickets, and verification checkpoints.

That plan should start with:

1. repository foundation and toolchain
2. base schema and migrations
3. seeds for sources and metric definitions
4. first structured connector and parse path
5. first textual connector and claim extraction path
6. feature builder
7. scoring and score evidence
8. tripwires, alerts, and narratives
