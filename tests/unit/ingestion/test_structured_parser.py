from __future__ import annotations

from datetime import date
from decimal import Decimal

from ai_thesis_monitor.ingestion.parsers.structured import parse_fred_rows


def test_parse_fred_rows_accepts_live_fred_csv_headers() -> None:
    rows = [
        {"observation_date": "2026-01-01", "UNRATE": "."},
        {"observation_date": "2026-01-15", "UNRATE": ""},
        {"observation_date": "2026-02-01", "UNRATE": "4.1"},
    ]

    assert parse_fred_rows(rows) == [
        {
            "observed_date": date(2026, 2, 1),
            "value": Decimal("4.1"),
        }
    ]
