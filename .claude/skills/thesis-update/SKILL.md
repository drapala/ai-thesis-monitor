---
name: thesis-update
trigger_keywords:
  - thesis-update
  - update theses
  - atualizar teses
  - check emergent thesis
  - verificar teses emergentes
  - which thesis is stronger
  - qual tese tá mais forte
  - citrini vs citadel
  - weekly thesis snapshot
description: >
  Refreshes the citadel/citrini scoring snapshot using REAL EMPIRICAL DATA via
  WebSearch — never parametric knowledge — with mandatory Bradford-respecting
  query distribution. Forces falsification probes (≥25% challenging queries
  against current lean) AND adjacent-possible probes (≥20% neither-side
  queries) so emergent third theses surface instead of being suppressed by
  confirmation bias. Output: updated metric values + lean classification +
  third-thesis candidate list with citations.
---

# thesis-update — Bradford-respecting thesis refresh from real data

## USE WHEN

- User asks "which thesis is stronger now?", "atualiza as teses", "thesis update"
- User wants weekly/monthly refresh of citadel-vs-citrini scoring
- User suspects an emergent third thesis but can't articulate it
- Before any external publication of thesis position (LinkedIn post, advisor memo)
- After any major macro event (Fed decision, big tech earnings, market dislocation)

## NOT WHEN

- User asks a specific factual question (answer directly, don't run full refresh)
- User wants implementation work on the monitor itself (use direct edits)
- User just wants a chart or visualization (different scope)
- Less than 7 days since last `thesis-update` run — diminishing returns, risk of
  noise-chasing. Override only with explicit reason.

## Hard rules (non-negotiable)

### 1. **Parametric knowledge is BANNED for evidence claims**

Every claim about employment, GDP, earnings, layoffs, SaaS distress, mortgage
rates, etc. MUST be sourced from a WebSearch result with a URL cited. If you
catch yourself writing a number or trend without a fresh URL backing it, stop
and search.

Why: model parametric knowledge has a training cutoff. Markets move daily.
Citing parametric data as "current" is the worst form of confidence inflation
for a thesis-comparison system.

### 2. **Bradford distribution is MANDATORY**

Use `ai-thesis-monitor adjacent-possible-plan --lean <current> --n <N>` to
generate the query plan FIRST. Don't free-form search. The plan enforces:

- ~30-45% queries confirming the current lean (tripwire detection)
- ~30-45% queries challenging the current lean (falsification — Bradford 25% min)
- ~20-30% adjacent-possible queries (neither side's terms — third-thesis discovery)

Failure mode this prevents: searching only for "confirming evidence" of whatever
the user (or you) currently believes. Observed 2026-05-10 with 100% citrini-loaded
queries — power bottleneck third thesis was only surfaced after Bradford
correction.

### 3. **Cite every empirical claim**

Output format requires `Sources:` section with markdown hyperlinks for EVERY
empirical claim. No exceptions. If a claim has no fresh URL, drop the claim or
mark it explicitly `[parametric — unverified]`.

### 4. **Surface emergent theses with their own row**

If 2+ adjacent-possible queries return evidence of a structural factor that
neither citadel nor citrini articulated, that's a candidate third thesis.
Surface it explicitly in output, don't fold it into either side's score.

Examples observed:
- Power/compute bottleneck (May 2026) — neither side's model
- Geopolitical chip decoupling — neither side's full model
- Open-source LLM deflation curve — neither side's full model

## Protocol

### Step 1 — Establish current lean

Run:

```bash
ai-thesis-monitor run-weekly --dry-run  # see current regime per module
# or read latest weekly snapshot if DB persisted
```

If no current scoring exists (cold start), default `current_lean = "neutral"`
and proceed.

### Step 2 — Generate Bradford-respecting query plan

```bash
ai-thesis-monitor adjacent-possible-plan \
  --lean <current_lean> \
  --n 15 \
  --output outputs/thesis-update-$(date +%F)/query-plan.md
```

Read the plan. Verify:
- ≥25% challenging queries against current lean
- ≥20% adjacent-possible queries
- No query duplicates last 14 days (check `outputs/thesis-update-*/`)

If distribution violates Bradford, regenerate or hand-edit before proceeding.

### Step 3 — Execute queries via WebSearch (parallel)

For each query in the plan, issue a WebSearch call. **Parallelize** — send all
queries in a single message as multiple tool calls.

Per query, extract:
- 3-5 concrete claims with URLs
- Date of source publication (reject anything older than 90 days unless
  explicitly historical — e.g., "Brynjolfsson 2025 study")
- Quantified data points (numbers > headlines)

### Step 4 — Apply metric updates

Map each empirical claim back to existing metrics in
`src/ai_thesis_monitor/db/seeds/metric_definitions.py`. Examples:

- "PE-backed SaaS distress" → `pe_saas_watchlist_distressed_pct` metric
- "30Y mortgage rate" → `mortgage_30y_rate` metric (FRED-pullable)
- "Power bottleneck" → `datacenter_capacity_delay_pct` metric (infrastructure module)

For each metric, propose:
- New value (or new observation row)
- Source URL
- Lag category respected (don't update a `confirmatory` metric on daily news)

If you find an empirical claim that has NO matching metric:
- Check if it fits an existing module — add new metric to that module
- If it doesn't fit any module — candidate for third-thesis emergence

### Step 5 — Detect emergent thesis candidates

For each adjacent-possible query response:
- Does the evidence point to a structural factor neither thesis models?
- Is the factor mentioned by 2+ independent sources?
- Does it have measurable proxies (FRED series, public reports)?

If yes, emit a third-thesis candidate with:
- Name (e.g. "power_bottleneck", "geopolitical_chip_decoupling")
- Mechanism (1-2 sentences)
- Why neither citadel nor citrini covers it
- Proposed metric(s) — FRED series IDs or manual proxies
- Module proposal (new module or fit to existing)

### Step 6 — Render output

Write to `outputs/thesis-update-$(date +%F).md` with structure:

```markdown
# Thesis update — YYYY-MM-DD

## Current regime
- Previous lean: <previous>
- New lean: <new>
- Confidence shift: <Δ>

## Bradford verification
- Confirming queries: N (X%)
- Challenging queries: N (X%)
- Adjacent-possible queries: N (X%)
- Bradford satisfied: yes/no

## Metric updates
| Metric | Old | New | Source |
|---|---|---|---|
| pe_saas_watchlist_distressed_pct | X% | Y% | [link] |
| ... |

## Emergent thesis candidates
### Candidate 1: <name>
- Mechanism: ...
- Sources: [link 1] [link 2]
- Proposed metrics: ...
- Module: ...

## Confirming evidence (current lean)
- ...

## Challenging evidence (against current lean)
- ...

## Sources
<full URL list>
```

### Step 7 — Commit + log

```bash
git add outputs/thesis-update-$(date +%F).md
git add src/ai_thesis_monitor/db/seeds/  # if metrics changed
git commit -m "thesis-update YYYY-MM-DD: <lean shift summary>"
```

Append decision to `docs/HUMAN-DECISION-LOG.md` (if it exists in this repo, or
adjacent vault path) with:
- Date, lean shift, top 2 metric movements, emergent thesis candidate (if any)

## Anti-patterns (do NOT do)

### "I'll just remember from last time"

You won't. Parametric knowledge stale. Re-search every empirical claim, even
ones you "know."

### "Skip Bradford, just confirm the current read"

This is the failure mode this skill exists to prevent. If Bradford distribution
isn't satisfied, the output is decorative, not epistemic. Regenerate.

### "Power bottleneck doesn't fit the citadel/citrini frame, ignore it"

Wrong. Emergent thesis candidates are the highest-value output. Folding them
into existing thesis scores destroys signal.

### "Use my training data for the macro overview, search just to fill gaps"

Inverted. Start from search. Only use parametric knowledge to interpret search
results, never to make claims.

### "12 queries is fine, no need for 15+"

n=12 is the floor, not target. For a thorough refresh, n=18-25. Cost: ~2-3
minutes of WebSearch in parallel. Worth it vs noise from undersampling.

## Capability decomposition check (run at end)

After producing output, append a 3-line self-audit:

```
% accumulated session context: X%
% Bradford-mandated falsification: X%
% base parametric capability: X%
```

If parametric capability is >15%, REDO. You're cheating.

## Examples of correct invocation

User: "atualiza as teses, qual tá mais forte?"

→ Run protocol. Default to `--lean neutral` if no current snapshot. n=15.
Execute all 15 queries via WebSearch in parallel. Cite every claim. Surface
any 2+-source emergent factor as third-thesis candidate.

User: "what's emerging that we're not tracking?"

→ Adjacent-possible heavy. Override n_queries to 70% adjacent. Output focuses
on candidates section, not metric updates.

User: "third-thesis check on power bottleneck"

→ Targeted: only adjacent-possible pool, with infrastructure-specific terms.
n=8-10. Output validates or falsifies the candidate's evidence base.

## References

- `src/ai_thesis_monitor/domain/adjacent_possible.py` — query plan generator
- `src/ai_thesis_monitor/db/seeds/metric_definitions.py` — metric registry
- `docs/superpowers/plans/2026-04-13-ai-thesis-monitor-v1.md` — original design
- Metaxon Bradford 25% quota for challenging — `/Users/drapala/projects/personal/metaxon/.claude/CLAUDE.md`

## Empirical pressure justifying this skill

On 2026-05-10, a thesis-comparison session produced 100% citrini-confirming
queries on the first pass. The user caught the Bradford violation. After
correction (5 confirming + 3 challenging + 4 adjacent-possible), a third
thesis surfaced (power/compute bottleneck) that neither citadel nor citrini
had modeled. This skill mechanizes the corrective step so future sessions
don't depend on the user catching the agent's confirmation bias.
