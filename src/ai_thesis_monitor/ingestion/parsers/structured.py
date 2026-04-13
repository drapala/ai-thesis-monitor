"""Parsers for structured economic source rows."""

from __future__ import annotations

from datetime import date
from decimal import Decimal


def parse_fred_rows(rows: list[dict[str, str]]) -> list[dict[str, date | Decimal]]:
    parsed: list[dict[str, date | Decimal]] = []
    for row in rows:
        value = row["VALUE"]
        if value == ".":
            continue
        parsed.append(
            {
                "observed_date": date.fromisoformat(row["DATE"]),
                "value": Decimal(value),
            }
        )
    return parsed
