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
]
