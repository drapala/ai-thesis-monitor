"""FRED CSV adapter."""

from __future__ import annotations

import csv
from io import StringIO

import httpx


class FredCsvAdapter:
    def __init__(self, *, base_url: str, client: httpx.Client) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client

    def fetch_series(self, *, series_id: str) -> list[dict[str, str]]:
        response = self._client.get(
            f"{self._base_url}/graph/fredgraph.csv",
            params={"id": series_id},
            timeout=30.0,
        )
        response.raise_for_status()
        rows = csv.DictReader(StringIO(response.text))
        return [dict(row) for row in rows]
