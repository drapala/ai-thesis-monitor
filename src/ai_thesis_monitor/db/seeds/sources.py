"""Source seed rows for reference data."""

from __future__ import annotations


SOURCE_SEED_ROWS: list[dict] = [
    {
        "source_key": "fred",
        "source_name": "Federal Reserve Economic Data",
        "source_type": "structured_csv",
        "base_url": "https://fred.stlouisfed.org",
        "config": {"path": "/graph/fredgraph.csv"},
        "reliability_score": 0.95,
        "active": True,
    },
    {
        "source_key": "rss_macro",
        "source_name": "Macro RSS Feed",
        "source_type": "rss",
        "base_url": "https://feeds.feedburner.com/CalculatedRisk",
        "config": {"kind": "macro"},
        "reliability_score": 0.85,
        "active": True,
    },
    {
        "source_key": "rss_corporate_ir",
        "source_name": "AI Claims RSS Feed",
        "source_type": "rss",
        "base_url": (
            "https://news.google.com/rss/search?q=%28AI%20layoffs%29%20OR%20"
            "%28reduce%20workforce%20AI%29%20OR%20%28SaaS%20pricing%20discounts%29%20OR%20"
            "%28AI%20build%20vs%20buy%29&hl=en-US&gl=US&ceid=US:en"
        ),
        "config": {"kind": "ai_claims"},
        "reliability_score": 0.82,
        "active": True,
    },
    {
        "source_key": "india_it_earnings",
        "source_name": "India IT Earnings (TCS/Infosys/Wipro/HCL)",
        "source_type": "manual",
        "base_url": "https://www.tcs.com/who-we-are/newsroom",
        "config": {
            "kind": "quarterly_earnings",
            "companies": ["TCS", "Infosys", "Wipro", "HCL"],
            "note": "Manually seeded from quarterly press releases. Proxy for white-collar labor and AI diffusion.",
        },
        "reliability_score": 0.90,
        "active": True,
    },
    # --- Expanded proxy sources (data pending fetch — see NEXT-ACTIONS.md) ---
    {
        "source_key": "cognizant_earnings",
        "source_name": "Cognizant Quarterly Earnings",
        "source_type": "manual",
        "base_url": "https://investors.cognizant.com",
        "config": {
            "kind": "quarterly_earnings",
            "note": "US-listed, India-heavy delivery. Bridge between India IT and US labor markets.",
        },
        "reliability_score": 0.85,
        "active": False,
    },
    {
        "source_key": "capgemini_earnings",
        "source_name": "Capgemini Quarterly Earnings",
        "source_type": "manual",
        "base_url": "https://investors.capgemini.com",
        "config": {
            "kind": "quarterly_earnings",
            "note": "European IT services. Tests whether India IT pattern replicates outside US/India.",
        },
        "reliability_score": 0.85,
        "active": False,
    },
    {
        "source_key": "accenture_earnings",
        "source_name": "Accenture Quarterly Earnings",
        "source_type": "manual",
        "base_url": "https://newsroom.accenture.com",
        "config": {
            "kind": "quarterly_earnings",
            "note": "Different fiscal year (Aug-Aug); often more recent data than India Big-4.",
        },
        "reliability_score": 0.90,
        "active": False,
    },
    {
        "source_key": "microsoft_earnings",
        "source_name": "Microsoft Azure AI / Copilot Disclosures",
        "source_type": "manual",
        "base_url": "https://www.microsoft.com/en-us/Investor",
        "config": {
            "kind": "quarterly_earnings",
            "note": "Demand-side counterpart to India IT supply. Copilot enterprise seat counts disclosed.",
        },
        "reliability_score": 0.95,
        "active": False,
    },
    {
        "source_key": "bls_eci",
        "source_name": "BLS Employment Cost Index",
        "source_type": "structured_csv",
        "base_url": "https://www.bls.gov/eci",
        "config": {
            "kind": "structured",
            "note": "White-collar wage growth. Series CIU2010000000000A (civilian comp) + CIU2020000000000A (professional).",
        },
        "reliability_score": 0.95,
        "active": False,
    },
    {
        "source_key": "indeed_hiring_lab",
        "source_name": "Indeed Hiring Lab AI-Exposed Postings",
        "source_type": "structured_csv",
        "base_url": "https://www.hiringlab.org",
        "config": {
            "kind": "structured",
            "note": "Free public dataset. Job postings index by occupation; AI-exposed slice.",
        },
        "reliability_score": 0.85,
        "active": False,
    },
    {
        "source_key": "nalp_law_hiring",
        "source_name": "NALP Law Firm Associate Hiring",
        "source_type": "manual",
        "base_url": "https://www.nalp.org/research",
        "config": {
            "kind": "annual_with_proxies",
            "note": "Annual NALP report; quarterly proxies via Above the Law / Big Law Investor.",
        },
        "reliability_score": 0.80,
        "active": False,
    },
    {
        "source_key": "transcript_mentions",
        "source_name": "Earnings Call Transcript AI/Automation Mentions",
        "source_type": "manual",
        "base_url": "https://seekingalpha.com",
        "config": {
            "kind": "text_mining",
            "note": "S&P 500 calls. Track 'AI', 'agent', 'automate', 'headcount reduction' frequency. Paid via AlphaSense/Sentieo, or DIY scrape.",
        },
        "reliability_score": 0.75,
        "active": False,
    },
]
