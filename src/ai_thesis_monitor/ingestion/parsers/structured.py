"""Parsers for structured economic source rows."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TypedDict


class FredParsedRow(TypedDict):
    observed_date: date
    value: Decimal


def parse_fred_rows(rows: list[dict[str, str]]) -> list[FredParsedRow]:
    parsed: list[FredParsedRow] = []
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
