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
        date_key = "DATE" if "DATE" in row else "observation_date"
        value_key = "VALUE" if "VALUE" in row else _infer_value_key(row)
        if date_key is None or value_key is None:
            continue

        value = row[value_key]
        if value in {".", ""}:
            continue
        parsed.append(
            {
                "observed_date": date.fromisoformat(row[date_key]),
                "value": Decimal(value),
            }
        )
    return parsed


def _infer_value_key(row: dict[str, str]) -> str | None:
    for key in row:
        if key not in {"DATE", "observation_date"}:
            return key
    return None
