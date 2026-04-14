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
        "source_name": "Corporate IR RSS Feed",
        "source_type": "rss",
        "base_url": "https://investor.servicenow.com/rss/news-releases.xml",
        "config": {"kind": "corporate"},
        "reliability_score": 0.82,
        "active": True,
    },
]

