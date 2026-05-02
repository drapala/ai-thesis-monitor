# Next Actions — Roadmap for Expanded Coverage

Generated 2026-05-02 alongside `TRENDS-2026-05-02.md`.

This document is the execution checklist for expanding the system beyond
the current India IT Big-4 + FRED proxies. Each item ranks: **value** (high/
medium/low for thesis discrimination), **effort** (hours), **cost** (free / paid),
**status** (stub-ready / needs-fetcher / blocked).

The structural plumbing is already in place:
- New metric definitions added to `metric_definitions.py`
- New source rows added to `sources.py` (all marked `active: False` until data lands)
- `seeds/expanded_proxy_data.py` has empty dicts ready to receive data
- Stub adapters: `bls_extended.py`, `indeed.py`, `transcripts.py`

What's missing is **data**. This file is the order of operations for getting it.

---

## Tier 1 — Same-shape extensions (highest leverage, lowest effort)

These reuse the `india_it_earnings` source pattern. Quarterly press releases,
manual seed, identical to how `seed-india-it-data` works today.

### 1. Per-company India Big-4 breakouts (Infosys, HCL specific)

- **Value**: medium. Detect divergence within India IT (e.g., Wipro accelerating, HCL stalling).
- **Effort**: ~30 min/quarter to add 4 quarters of Infosys + HCL headcount.
- **Cost**: free. Press releases are public.
- **Status**: stub-ready. Metric keys `infosys_headcount`, `hcl_headcount` defined.
- **Sources**:
  - Infosys: https://www.infosys.com/investors/reports-filings/quarterly-results/
  - HCL: https://www.hcltech.com/investors/results-reports
- **Action**: open seed file, add 4-6 quarters of headcount per company starting with FY25 baseline. Mirror the `quality_score` convention (0.90 confirmed / 0.70 approx).

### 2. Cognizant (US-listed bridge, India-heavy delivery)

- **Value**: high. Cross-checks if India IT compression generalizes to US-listed peers.
- **Effort**: ~45 min for 6 quarters of headcount + AI revenue %.
- **Cost**: free. 10-Q filings are public.
- **Status**: stub-ready. Metrics `cognizant_headcount`, `cognizant_ai_revenue_pct` defined.
- **Source**: https://investors.cognizant.com/financials/quarterly-results
- **Action**: pull last 6 quarterly 10-Qs, extract employee count + AI revenue commentary. Note: Cognizant began breaking out "Cognizant Neuro" / GenAI revenue in CY2026 Q1 — that's the first hard datapoint.

### 3. Capgemini (European IT services regression test)

- **Value**: medium-high. Tests geographic generalizability of the India IT pattern.
- **Effort**: ~30 min for 4 half-year reports.
- **Cost**: free.
- **Status**: stub-ready. Metric `capgemini_headcount` defined.
- **Source**: https://investors.capgemini.com/en/financial-publications
- **Note**: Capgemini reports half-yearly (March + September), not quarterly — granularity is lower than India Big-4.

### 4. Accenture (different fiscal year — earlier data point each cycle)

- **Value**: high. Earliest forward signal in each quarterly cycle (fiscal years offset).
- **Effort**: ~45 min for 6 quarters.
- **Cost**: free for headcount + qualitative GenAI mentions; **paid or scraped** for specific GenAI bookings dollars.
- **Status**: stub-ready. Metrics `accenture_headcount`, `accenture_genai_bookings_pct` defined.
- **Source**: https://newsroom.accenture.com/news/quarterly-earnings/
- **Note as of 2026-05-02**: Q2 FY26 (Feb 28 2026) released Mar 19 2026 — qualitative signals only ("revenue at top of guided range", "record new bookings", FY26 guidance raised to 3-5%). Specific dollar amounts gated behind 10-Q PDF.

---

## Tier 2 — New source pattern (medium leverage, requires adapter work)

### 5. BLS Employment Cost Index (white-collar wages)

- **Value**: high. Critical citrini test — wage growth stagnating while productivity rises = employer captures gains. Distinguishes the two theses cleanly.
- **Effort**: ~2 hours to wire adapter + ~30 min/quarter for ongoing maintenance.
- **Cost**: free.
- **Status**: adapter stub at `ingestion/adapters/bls_extended.py`. Series IDs documented. Wraps existing FredAdapter pattern.
- **Action**:
  1. Implement `fetch_bls_series` in `bls_extended.py` (use `FredAdapter` pattern from `fred.py`)
  2. Add CLI command `seed-bls-extended-data` in `cli/main.py`
  3. Run for series CIU2020000000000A — backfill 8+ quarters
  4. Verify output via `replay-week` for past month

### 6. Microsoft Copilot enterprise seats / Azure AI revenue

- **Value**: high. Demand-side counterpart to India IT supply. Direct AI penetration signal.
- **Effort**: ~30 min/quarter, manual (numbers come out of earnings call commentary, not 10-Q).
- **Cost**: free.
- **Status**: stub-ready. Metrics defined.
- **Source**: https://www.microsoft.com/en-us/Investor/earnings/
- **Action**: per quarter, listen to / read earnings call transcript, capture specific Copilot seat number when CFO mentions a milestone (e.g., "X million seats"). Azure AI growth typically given as YoY % in same call.

### 7. Indeed AI-exposed postings index

- **Value**: high. Leading indicator vs Harvard's lagging hiring study. Weekly cadence = much faster signal than quarterly proxies.
- **Effort**: ~3 hours initial setup + automatic from there.
- **Cost**: free.
- **Status**: adapter stub at `ingestion/adapters/indeed.py`. Occupation list defined. CSV source documented (`hiring-lab/data` GitHub).
- **Action**:
  1. Confirm exact CSV filenames in https://github.com/hiring-lab/data
  2. Implement weighted-index aggregation
  3. Wire CLI `seed-indeed-data` (or run-daily integration)

---

## Tier 3 — Higher friction, higher uniqueness

### 8. Earnings call transcript mentions ('AI', 'headcount reduction')

- **Value**: high. The "headcount reduction" mention count is **citrini-direct rhetoric** — no other signal in the system measures explicit corporate intent to compress white-collar.
- **Effort**: ~6 hours initial + ~2 hours/quarter ongoing.
- **Cost**: paid (~$50-100/quarter via API) OR free (DIY scrape, slow).
- **Status**: adapter stub at `ingestion/adapters/transcripts.py`. Term families defined. `count_mentions()` implemented for offline use.
- **Sources** (pick one):
  - **AlphaSense API** (~$10K+/year) — best, gives clean transcripts
  - **Sentieo** (~$5K+/year) — second tier
  - **Seeking Alpha** (free but rate-limited)
  - **DIY**: SEC EDGAR 8-K + company IR PDFs
- **Action**:
  1. Choose source. For solo use, recommend DIY → top-50 S&P 500 by market cap, quarterly.
  2. Build fetcher in `transcripts.py`
  3. Wire CLI `seed-transcript-mentions`
  4. Backfill 4 quarters

### 9. Big Law associate hiring (NALP)

- **Value**: medium. Premium white-collar canary. Annual cadence is slow, but lower-frequency proxies via Above the Law / Big Law Investor.
- **Effort**: ~1 hour annually + ~30 min/quarter for proxy.
- **Cost**: free (NALP report public; ATL/BLI publicly accessible).
- **Status**: stub-ready. Metric `biglaw_associate_offers_yoy` defined.
- **Source**: https://www.nalp.org/research
- **Note**: lowest cadence + smallest sample of any metric. Treat as confirmation, not leading.

### 10. Big-4 audit/consulting hiring (Deloitte/EY/KPMG/PwC)

- **Value**: medium. Sector-specific signal — these firms publicly announced cuts in 2024-25, would be nearly unique to track quarterly hires.
- **Effort**: ~2 hours/quarter (firms are private; data scattered across press releases + LinkedIn employee counts).
- **Cost**: free but tedious.
- **Status**: NOT yet defined. Add a metric `big4_audit_hires_yoy` if you commit to this.
- **Action**: defer until at least 5 quarters of Tier 1 data accumulated to anchor analysis.

---

## Anti-recommendations (do NOT add)

- ❌ **OpenAI / Anthropic specific revenue** — too narrow, too noisy. Macro signal != startup leak. Skip.
- ❌ **Stock prices** as signals — already priced in, lagging-confirmatory not leading. The thesis monitor should SHAPE expectation, not confirm market.
- ❌ **Twitter/X sentiment AI** — vibes, not regime. Adds noise.
- ❌ **WPP/Publicis (advertising creative)** — real AI exposure but pre-existing ad-recession confounds the AI signal. Save for post-1-year analysis.

---

## Bradford balance check (current state, 2026-05-02)

System is **citadel-leaning** based on India IT data alone:
- Productivity rising (TCS rev/emp +14% over 2y, Wipro util +2pp)
- Labor compression real but partial recovery in Q4 FY26
- AI revenue diffusion linear, not crashing

To honor the 25% challenging quota, the **next 1-2 ingests should be citrini-strengthening**:

1. **BLS ECI** (Tier 2 #5) — if wage growth stagnates while productivity rises, citrini gains hard evidence
2. **Earnings call "headcount reduction" mentions** (Tier 3 #8) — direct rhetoric measure
3. **Indeed AI-exposed YoY** (Tier 2 #7) — leading indicator of compression

If citadel STILL wins after these 3 land, the thesis is robust. If citrini reverts, balance shifts honestly.

---

## Recommended execution order

**This week (high-leverage low-effort):**
1. Tier 1 #1: Infosys + HCL specifics (30 min)
2. Tier 1 #2: Cognizant 6 quarters (45 min)

**Next 2 weeks (medium effort, unlocks new modules):**
3. Tier 2 #5: BLS ECI adapter (2 hr) — fills `productivity` + `labor` modules at macro level
4. Tier 2 #6: Microsoft Copilot quarterly (30 min × 6 quarters = 3 hr)

**Month 2 (defer until system has 1-2 weeks of operation):**
5. Tier 2 #7: Indeed adapter (3 hr)
6. Tier 1 #4: Accenture quarterly (45 min × 4 quarters)

**Quarter 2 (only if citrini balance still inadequate):**
7. Tier 3 #8: Earnings call transcript text mining
8. Tier 1 #3: Capgemini half-yearly

**Defer indefinitely (until value justifies):**
9. Tier 3 #9: Big Law associate hiring
10. Tier 3 #10: Big-4 audit hiring

---

## What this work UNLOCKS

After Tier 1 + Tier 2 ingest:
- `diffusion` module: 6 independent signals (currently 4)
- `productivity` module: macro BLS + per-company India IT (currently India IT only)
- `labor` module: macro BLS unemployment + per-company headcount + Indeed YoY (currently aggregate India IT + macro placeholder)
- `demand`, `intermediation`, `credit_housing` — STILL need separate ingest pipelines (FRED for macro, RSS for corporate text)

---

## Caveats from 2026-05-02 generation

- All numbers in metric definitions are **schema only**, not data. The `expanded_proxy_data.py` dict is empty by design. **DO NOT FABRICATE** when populating; mark approximations with quality_score 0.50-0.70.
- Web fetches to IR pages (Accenture, TCS, Reuters) hit 403/404 during the planning session — manual PDF download will be needed.
- Per-quarter maintenance cost across all Tier 1+2: ~3-5 hours every quarterly earnings season. Can be batched in one weekend.
