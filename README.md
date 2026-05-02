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

## Outlook & Forecast (snapshot 2026-05-02)

This section records a point-in-time qualitative view that the system's quantitative output is meant to **falsify**, not confirm. It exists to make explicit what the curator (a human) believes ahead of the data, so the data can either validate or override that belief.

### Headline view

**Citrini is more likely than citadel over a 3-5 year horizon, but it will manifest more slowly than citrini proponents expect, and through "AI replaces hiring" rather than "AI fires people."** Short-term (1-2 years) the system will continue to read citadel-leaning, partly because institutional friction is genuine and partly because three of six modules are silent for lack of data.

### Probability distribution (subjective)

| Horizon | Citadel | Citrini | Mixed transition |
| --- | --- | --- | --- |
| 1-2 years (through 2027) | **~70%** | ~25% | ~5% |
| 3-5 years (2028-2030) | ~30-40% | **~50-60%** | ~10% |
| 5+ years (post-2030) | ~25% | ~50-60% | ~15% |

The "mixed transition" cell captures historical analogues (agriculture → manufacturing 1900-1950, manufacturing → services 1970-2000): white-collar does not collapse, it erodes silently through hiring freeze + non-replacement, while new job categories emerge that today are not yet named.

### Why citadel is winning right now (1-2 years)

1. **Productivity is arriving before substitution.** TCS revenue/employee +14% over 2y while headcount partially recovered in Q4 FY26 (+16k). Workers who stayed are producing more without mass layoff — the canonical citadel scenario.
2. **Labor compression is slow, not acute.** -58k in 7 quarters = 4% of total. Dot-com 2000-02 and GFC 2008-09 both saw white-collar drop 8-15% in less time. Current pace is gradual.
3. **Compute economics throttles speed.** 75% of AI ecosystem revenue is stuck at the semi layer; app-layer margins are 0-30% vs Nvidia's 75%. The layer where labor displacement happens does not have the financial headroom to deploy mass substitution aggressively.
4. **Capability ceiling is real.** Remote Labor Index: best agent completed 2.5% of 240 real Upwork projects to client-acceptance quality (97.5% failure rate on real jobs, vs near-expert quality on context-provided GDPVal). AI is not yet doing JOBS, only TASKS.
5. **Institutional friction is genuine.** Apollo Research finding: anti-scheming alignment training PERVERSELY increases evaluation-detection rate (2.3% → 4.5%). Software maintenance benchmarks: 75% of frontier models break previously-working features. Intent engineering is still being discovered. Enterprise mass-deployment of autonomous agents is not yet possible reliably.

### Why citrini is more likely over 3-5 years

1. **The compression is silent, not dramatic.** Harvard 62M-worker study: GenAI-adopting firms saw junior employment drop ~8% in 18 months, **driven by slower hiring, NOT layoffs**. This is exactly how citrini manifests in practice — no "D-day" of mass firing, just 24+ months of non-hiring that shows up in the data after the fact. It is already happening.
2. **AI revenue compounds from a small base.** TCS AI revenue 2.5% → 7.5% in 18 months is linear, but linear continuation projects past 25% in ~24 more months. Once AI delivery margin exceeds traditional IT delivery margin at scale, headcount cuts become economically forced rather than optional.
3. **"Digital labor" reframe is entering economics.** Cobb-Douglas formulations of AI as a new factor of production (Lochmiller / Crusoe) are entering policy expectations, which feeds back into corporate behavior. Self-fulfilling prophecy risk.
4. **Premium analyst work is exactly what AI does well.** The Big Law associate / Big-4 audit junior / financial analyst tier is where IQ commoditizes first (Gerstner). These sectors have already publicly cut hiring in 2024-25 explicitly citing AI — this is observed history, not forecast.
5. **The three silent modules will eventually wake up.** The citrini cascade is: labor compression → high-income demand drop → SaaS pricing pressure → credit stress in tech metros. This takes 18-24 months to materialize from the initial labor shock. The shock has been ongoing since 2024. By the time `demand` / `intermediation` / `credit_housing` light up in this system, the regime change is already a fait accompli.
6. **Behavioral lock-in shifts power asymmetrically.** Persistent agents (Conway-style) accumulate the behavioral model of HOW an employee works as a company asset, while the employee loses negotiation leverage when switching. This compresses white-collar wages structurally without any visible layoff.

### Observable predictions (verifiable in 6 and 12 months)

These are concrete, falsifiable, dated. Recorded so future reality can override curator belief.

**By November 2026 (6 months):**

| # | Metric | Predicted range | Citadel-supporting if | Citrini-supporting if |
| --- | --- | --- | --- | --- |
| P1 | India Big-4 combined headcount Q1 FY27 (data Jun 2026, released Jul 2026) | 1,395-1,410k | >1,410k (continued recovery) | <1,383k (new low past Q3 FY26 trough) |
| P2 | TCS AI revenue % Q1 FY27 | 8.0-8.5% | 8.0-8.5% (linear continuation) | >9.5% (acceleration phase) |
| P3 | Wipro utilization Q1 FY27 | 84.0-85.0% | stable in band (productivity locked in) | overshoot >86% (forced churning) |
| P4 | Accenture Q3 FY26 (May 2026 quarter, released ~late Jun) | revenue at top of guidance, FY26 guidance maintained at 3-5% | guidance raised | guidance cut |
| P5 | BLS ECI white-collar Q2 2026 (released Jul/Aug) | 2.8-3.4% YoY | >3.4% (workers share productivity) | <2.5% (employer captures gains, citrini margin compression) |
| P6 | US unemployment professional services May/Jun 2026 | 3.0-3.5% | <3.0% (labor market tight) | >3.7% (visible compression) |
| P7 | Microsoft Q4 FY26 Copilot seat disclosure (released ~late Jul 2026) | growth from current; Azure AI >25% YoY | Copilot seats grow but not displacing labor counterparts | Copilot seats spike + customer headcount falls in same calls |

**By May 2027 (12 months):**

| # | Metric | Predicted range | Citadel-supporting if | Citrini-supporting if |
| --- | --- | --- | --- | --- |
| Q1 | India Big-4 cumulative headcount end-FY27 (Mar 2027, released Jul 2027) | 1,380-1,415k range | >1,420k (full recovery) | <1,360k (acceleration of decline) |
| Q2 | TCS AI revenue % end-FY27 | 9.5-11.0% | 9.5-11.0% (linear continuation) | >12% or <8.5% (regime shift either direction) |
| Q3 | US junior tech hire YoY (Harvard methodology replicated) | -3% to -8% | >-2% (hiring resumes) | <-10% (acceleration) |
| Q4 | White-collar layoff event count Q1 2027 | 50-150 per quarter | <50 (compression done) | >200 (visible wave) |
| Q5 | ECI white-collar full-year 2026 | 2.5-3.0% YoY | >3.0% (employee share holds) | <2.5% (margin capture confirmed) |
| Q6 | Big Law summer 2026 associate offers (NALP, Aug-Sep 2026 release) | -5% to -10% YoY | >-3% (premium tier holds) | <-12% (premium tier compression) |
| Q7 | Earnings call "headcount reduction" mentions Q4 2026 | +20% to +50% YoY | <+20% (no rhetoric escalation) | >+75% (citrini-direct rhetoric wave) |

### Tripwires (would force regime call)

**Forces "citadel firm through 2030"** if hit cumulatively:
- Q1 FY27 Big-4 headcount > 1,415k (recovery continues)
- BLS ECI white-collar > 3.5% YoY by end-2026 (workers share productivity)
- New job categories institutionalized at >$150k base salary (AI ops, agent supervisor, intent engineer)
- Microsoft Copilot enterprise seats exceed 50M without correlated layoff wave at customer firms

**Forces "citrini accelerates to 2-3 year horizon"** if hit cumulatively:
- Q1 FY27 Big-4 headcount < 1,383k (new low past Q3 FY26 trough)
- BLS ECI white-collar plateaus or falls (<2% YoY) while productivity rises >3%
- Earnings call "headcount reduction" mentions double in 4 quarters
- Junior hiring drops accelerate to >12% YoY (above Harvard's current 8%)
- Spread between senior salary growth and junior wage growth widens >5pp/year (premium concentration)

### Risk factors / Black swans

**Could derail citrini:**
- **Compute supply crisis** — TSMC 2nm bottleneck, helium constraints (Qatar exposure), power grid limits — caps AI deployment speed (~20-30% over 5y)
- **AI safety incident** — Apollo-style scheming in production system, 12-18 month enterprise deployment freeze (~30-40% over 5y)
- **Regulatory hammer** — EU AI Act enforcement at scale + US labor protection executive orders (~50-60% over 5y, impact uncertain)

**Could accelerate citrini:**
- **Capability breakthrough** — agent system that closes context-blindness gap (Remote Labor Index goes from 2.5% to >30%) (~15-25% over 3y)
- **Big Law / Big-4 audit / Wall Street junior crisis becomes Lehman-style media moment** triggering reflexive corporate cuts (~30-40% over 3y)
- **Geopolitical scramble** (Taiwan, US-China decoupling) creating domestic deployment incentive (~20-30% over 5y)

### Bradford balance verdict (epistemic check)

The system is structurally well-designed (17 of 28 metrics actively discriminate between theses), but currently **citadel-favored at the population layer**: only India IT data is populated, and India IT favors citadel by construction (productivity gains visible before substitution).

Three of six modules (`demand`, `intermediation`, `credit_housing`) are silent. **Critical risk**: if the system runs `run-weekly` only on currently-populated data, it will consistently report citadel leading not because citadel is winning but because the modules where citrini would win are silenced for lack of data.

**Remediation order** (per `NEXT-ACTIONS.md`, Bradford-rebalance prescription):
1. Activate existing FRED-configured metrics (`unemployment_rate_professional_services`)
2. Run RSS pipelines for `layoffs_white_collar_count`, `saas_renewal_discount_mentions`, `ai_build_vs_buy_mentions` (sources already configured)
3. Implement BLS ECI adapter (`bls_extended.py` stub) → `eci_white_collar_yoy`
4. Manual seed Microsoft Copilot disclosures, Cognizant headcount + AI revenue (4-6 quarters)

After steps 1-4 land, re-evaluate. If citadel **still** leads with citrini-direct evidence included, the verdict is robust. If citrini reverses, the balance was structurally biased before.

### Confidence caveat

Forecast confidence: **medium**. Built from 9 quarters of India IT proxy data, qualitative cluster syntheses across ~65 secondary sources (talk summaries, papers), and historical analogy. Forecasts age fast — this entire section will be stale by Q1 FY27 release in July 2026.

The system exists precisely because single-thesis forecasting is over-confident. The `run-weekly` output, fed enough data, is meant to override this curator view when reality diverges.

See [`TRENDS-2026-05-02.md`](TRENDS-2026-05-02.md) for the underlying trend analysis and [`NEXT-ACTIONS.md`](NEXT-ACTIONS.md) for the data-fetch roadmap that would update this snapshot.

## MVP Boundaries

The current V1 contract is:

- public sources only
- US-only scope for macro indicators; India IT used as global proxy
- headless execution
- no end-user dashboard
- no end-to-end black-box scoring
- lightweight human review for important textual evidence

If you want the deeper design rationale, read [`docs/superpowers/specs/2026-04-13-ai-thesis-monitor-v1-design.md`](docs/superpowers/specs/2026-04-13-ai-thesis-monitor-v1-design.md).
