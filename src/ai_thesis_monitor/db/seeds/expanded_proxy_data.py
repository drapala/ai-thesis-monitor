"""Expanded proxy seed data — Cognizant, Capgemini, Accenture, Microsoft, BLS, etc.

STATUS: structure-only. NO DATA POINTS YET. Each metric key has an empty list,
ready to receive real numbers once you have IR PDF access / paid data sources /
public CSVs.

Data must be sourced manually per the rule from `india_it_data.py`:
- quality_score=0.90 for confirmed numbers from primary source (press release, 10-Q)
- quality_score=0.70 for approximated intermediate quarters
- quality_score=0.50 for qualitative-only (e.g., "revenue at top of guided range")
- quality_score=0.0 for placeholder rows (don't fabricate; leave empty)

See `NEXT-ACTIONS.md` at repo root for fetching priorities and sources.

Companies / sources covered by this file:
- Cognizant (US-listed, India-heavy delivery)
- Capgemini (European IT services)
- Accenture (different fiscal year than India Big-4)
- Microsoft (demand-side: Copilot seats, Azure AI revenue)
- Per-company India IT breakouts (Infosys, HCL — currently aggregated only)
- BLS Employment Cost Index (white-collar wages)
- Indeed Hiring Lab AI-exposed postings
- Big Law associate hiring (NALP)
- S&P 500 earnings call transcript mentions (AI/automation/headcount-reduction)
"""

from __future__ import annotations

from datetime import date  # noqa: F401  (kept for when data lands)
from decimal import Decimal  # noqa: F401  (kept for when data lands)


# Each row: (observed_date, value, quality_score, notes)
# Match shape of INDIA_IT_DATA in india_it_data.py.
# Empty lists = no data yet. DO NOT add fabricated rows.

EXPANDED_PROXY_DATA: dict[str, list[tuple]] = {
    # --- Per-company India Big-4 breakouts ---
    "infosys_headcount": [
        # TODO: Infosys quarterly press releases publish "people" count.
        # FY26 Q4 (Mar 31 2026, released Apr 16 2026): expected ~317k
        # FY26 Q3 (Dec 31 2025): expected ~316k
        # Source: https://www.infosys.com/investors/reports-filings/quarterly-results/
    ],
    "hcl_headcount": [
        # TODO: HCL Technologies quarterly press releases publish total employees.
        # FY26 Q4 (Mar 31 2026, released Apr 21 2026): expected ~228k
        # Source: https://www.hcltech.com/investors/results-reports
    ],
    # --- Cognizant (US-listed bridge) ---
    "cognizant_headcount": [
        # TODO: 10-Q quarterly filing reports global employee count.
        # CY2026 Q1 (Mar 31 2026, released ~May 1 2026): expected ~336k
        # Source: https://investors.cognizant.com/financials/quarterly-results
    ],
    "cognizant_ai_revenue_pct": [
        # TODO: Cognizant began breaking out AI-driven revenue in CY2026 Q1 earnings call.
        # Look for "Generative AI" or "Cognizant Neuro" specific revenue mention.
        # Source: 10-Q filing + earnings call transcript
    ],
    # --- Capgemini (European IT services) ---
    "capgemini_headcount": [
        # TODO: Half-year reports (March + September). Capgemini reports total people.
        # H1 2026 (released ~Jul 30 2026): expected ~340k
        # H2 2025 (released ~Feb 14 2026): ~340k
        # Source: https://investors.capgemini.com/en/financial-publications
    ],
    # --- Accenture (different fiscal year — quarterly: Aug/Nov/Feb/May) ---
    "accenture_headcount": [
        # TODO: 10-Q discloses people count.
        # Q2 FY26 (Feb 28 2026): expected ~775k (released Mar 19 2026)
        # Q3 FY26 (May 31 2026): not yet released as of 2026-05-02
        # Source: https://newsroom.accenture.com/news/quarterly-earnings/
    ],
    "accenture_genai_bookings_pct": [
        # TODO: Accenture discloses GenAI bookings each quarter on earnings call.
        # Q2 FY26 (Feb 28 2026): qualitative only ("record new bookings")
        # specific numbers gated behind 10-Q PDF — needs scrape
    ],
    # --- Microsoft (demand-side counterpart) ---
    "microsoft_copilot_seats": [
        # TODO: Microsoft sometimes discloses enterprise Copilot seat numbers in earnings calls.
        # Q3 FY26 (Mar 31 2026, released Apr 23 2026): qualitative + selected datapoints in call
        # Most reliable when CFO mentions specific milestones (e.g., "X million seats")
        # Source: https://www.microsoft.com/en-us/Investor/earnings/
    ],
    "microsoft_azure_ai_revenue_yoy": [
        # TODO: Azure overall growth disclosed quarterly; AI services slice needs commentary.
        # FY26 Q3: Azure growth expected ~30%+, AI services contribution called out separately
    ],
    # --- BLS Employment Cost Index (white-collar wages) ---
    "eci_white_collar_yoy": [
        # TODO: Auto-fetchable via FRED extension. Series CIU2020000000000A
        # (employment cost index, civilian workers, professional and related occupations,
        # private industry, all benefits, percent change YoY).
        # Released quarterly, ~end of month following quarter close.
        # Q1 2026 release: end of April 2026 (just released).
        # Use bls_extended adapter once implemented.
    ],
    # --- Indeed Hiring Lab AI-exposed postings ---
    "indeed_ai_exposed_yoy": [
        # TODO: Free public dataset at https://www.hiringlab.org/wp-content/uploads/
        # Indeed publishes weekly postings index by occupation; AI-exposed slice
        # requires defining the occupation list (typically: paralegal, financial analyst,
        # marketing analyst, software developer entry-level, customer service, copywriter).
        # Build via indeed.py adapter once implemented.
    ],
    # --- Big Law associate hiring (NALP) ---
    "biglaw_associate_offers_yoy": [
        # TODO: Annual NALP Perspectives on Summer Associate report (Aug-Sep release).
        # Quarterly proxy via Above the Law / Big Law Investor scraping.
        # NALP 2024 (FY24 hiring): ~6,500 summer associate offers at Vault 100
        # NALP 2025 (FY25 hiring): expected lower; reports of restraint
    ],
    # --- Earnings call transcript mentions ---
    "earnings_call_ai_mentions_yoy": [
        # TODO: text-mining S&P 500 quarterly calls.
        # Sources (paid): AlphaSense, Sentieo, FactSet
        # Sources (free): Seeking Alpha (rate-limited), company IR transcripts (manual)
        # Track terms: "AI", "artificial intelligence", "agent", "automate", "automation"
        # Build via transcripts.py adapter once implemented.
    ],
    "earnings_call_headcount_reduction_mentions": [
        # TODO: same source as above. Track terms:
        # "headcount reduction", "workforce optimization", "rightsizing",
        # "operational efficiency program", "restructuring".
        # Citrini-direct: rising count = explicit AI-driven labor compression rhetoric.
    ],
}
