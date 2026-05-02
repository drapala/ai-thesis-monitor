"""Indeed Hiring Lab adapter — AI-exposed job postings index.

STATUS: stub. Indeed Hiring Lab publishes free, weekly job postings indices
broken out by occupation. The "AI-exposed" slice has to be constructed by
combining specific occupation series.

Source:
- Public CSV downloads: https://github.com/hiring-lab/data
- Aggregator page: https://www.hiringlab.org

Occupations recommended for AI-exposed bucket (per recent papers / Brookings):
- Paralegal & Legal Assistants
- Financial Analyst
- Marketing Analyst / SEO Specialist
- Software Developer (entry-level / junior tier)
- Customer Service Representative
- Copywriter / Content Writer
- Bookkeeping / Accounting Clerk

Mechanics:
- Indeed publishes weekly index = (postings this week / postings Feb-2020 baseline) * 100
- AI-exposed bucket = weighted average of the above series
- YoY computation = compare 4-week trailing avg to same 4 weeks last year

Cost: free.

To implement:
1. Subscribe / pull occupation CSVs from the GitHub repo (hiring-lab/data)
2. Define the occupation list as config (likely in sources.py)
3. Compute weighted index per week
4. Surface via metric_key="indeed_ai_exposed_yoy"
5. Wire CLI command `seed-indeed-data` (or run-daily).
"""

from __future__ import annotations


# Default occupation list for the AI-exposed bucket.
# Each entry: (occupation_label, hiringlab_csv_filename, weight)
AI_EXPOSED_OCCUPATIONS: list[tuple[str, str, float]] = [
    ("paralegal_legal_assistant", "TODO_paralegal_index.csv", 1.0),
    ("financial_analyst", "TODO_financial_analyst_index.csv", 1.0),
    ("marketing_analyst", "TODO_marketing_analyst_index.csv", 1.0),
    ("software_developer_entry", "TODO_software_developer_entry_index.csv", 1.5),
    ("customer_service", "TODO_customer_service_index.csv", 0.8),
    ("copywriter", "TODO_copywriter_index.csv", 1.2),
    ("bookkeeping_clerk", "TODO_bookkeeping_clerk_index.csv", 0.8),
]


def fetch_ai_exposed_index() -> list[dict]:
    """Fetch the constructed AI-exposed postings index. NOT YET IMPLEMENTED.

    Returns weekly weighted index series.
    """
    raise NotImplementedError(
        "indeed adapter is a stub. See AI_EXPOSED_OCCUPATIONS list + Indeed Hiring "
        "Lab GitHub (hiring-lab/data) for the actual CSV filenames. Implementation "
        "is straightforward CSV download + weighted average."
    )
