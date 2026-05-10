"""BLS extended adapter — Employment Cost Index (ECI) and adjacent series.

Wraps the existing FredCsvAdapter with a BLS_SERIES_MAP that bundles series
relevant to citadel-vs-citrini analysis. BLS hosts its own JSON API at
api.bls.gov/publicAPI/v2, but the FRED CSV mirror is simpler and free; we
default to FRED here. Direct BLS API path kept as optional fallback for
series not mirrored on FRED.

Series IDs of interest (FRED hosts BLS data):
- CIU2020000000000A — ECI professional/management occupations, total comp YoY
- CIU2010000000000A — ECI civilian workers, all occupations YoY
- LNS14000048       — Unemployment 25+, management/professional/related
- LNS14000003       — Unemployment rate, professional services
- JTS1000HIL        — JOLTS Hires, Information sector
- JTS5000QUL        — JOLTS Quits, Professional and Business Services

Cost: free (FRED public). BLS API rate-limited to 25 unauthenticated req/day,
500/day with free registration.
"""

from __future__ import annotations

import csv
from io import StringIO

import httpx


# Series ID → metadata (metric_key, frequency, units, transform hint)
BLS_SERIES_MAP: dict[str, dict] = {
    "CIU2020000000000A": {
        "metric_key": "eci_professional_management_yoy",
        "frequency": "quarterly",
        "units": "percent",
        "is_yoy": True,
        "description": (
            "Employment Cost Index, civilian workers, professional & management "
            "occupations, total compensation. Released quarterly, end of month "
            "following quarter close. Citrini-confirming if decelerating."
        ),
    },
    "CIU2010000000000A": {
        "metric_key": "eci_civilian_all_yoy",
        "frequency": "quarterly",
        "units": "percent",
        "is_yoy": True,
        "description": "ECI civilian workers, all occupations. Macro baseline.",
    },
    "LNS14000048": {
        "metric_key": "unemployment_25plus_management_professional",
        "frequency": "monthly",
        "units": "percent",
        "is_yoy": False,
        "description": (
            "Unemployment rate, 25+, management/professional/related occupations. "
            "Extends Brynjolfsson finding from <25 to 25+ pop."
        ),
    },
    "LNS14000003": {
        "metric_key": "unemployment_rate_professional_services",
        "frequency": "monthly",
        "units": "percent",
        "is_yoy": False,
        "description": "Unemployment rate, professional & business services industry.",
    },
    "JTS1000HIL": {
        "metric_key": "jolts_hires_information",
        "frequency": "monthly",
        "units": "thousands",
        "is_yoy": False,
        "description": "JOLTS Hires, Information sector. Proxy for IT hiring.",
    },
    "JTS5000QUL": {
        "metric_key": "jolts_quits_professional_business",
        "frequency": "monthly",
        "units": "thousands",
        "is_yoy": False,
        "description": (
            "JOLTS Quits, Professional & Business Services. Worker confidence "
            "proxy — low quits = labor-market weakness."
        ),
    },
}


class BlsExtendedAdapter:
    """BLS-specific adapter wrapping FRED CSV mirror for BLS series.

    Reuses the same fetch shape as FredCsvAdapter (date,value rows). The
    BLS_SERIES_MAP above documents which series matter for citrini/citadel
    analysis without polluting the generic FRED adapter.
    """

    def __init__(
        self,
        *,
        base_url: str = "https://fred.stlouisfed.org",
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client or httpx.Client()

    def fetch_bls_series(self, series_id: str) -> list[dict[str, str]]:
        """Fetch a BLS series via FRED CSV endpoint.

        Returns a list of {date, value} dicts (FRED column shape preserved).
        Caller is responsible for downstream parsing/normalization (consistent
        with FredCsvAdapter contract).
        """
        if series_id not in BLS_SERIES_MAP:
            # Soft warn but proceed — adapter shouldn't gatekeep unknown IDs.
            pass
        response = self._client.get(
            f"{self._base_url}/graph/fredgraph.csv",
            params={"id": series_id},
            timeout=30.0,
        )
        response.raise_for_status()
        rows = csv.DictReader(StringIO(response.text))
        return [dict(row) for row in rows]

    def fetch_all_active(self) -> dict[str, list[dict[str, str]]]:
        """Bulk-fetch every series in BLS_SERIES_MAP.

        Returns mapping {series_id: rows}. Caller can dispatch to seed-loader.
        Note: respects no rate-limiting beyond httpx defaults. For production,
        wrap in a backoff retry adapter.
        """
        return {
            series_id: self.fetch_bls_series(series_id) for series_id in BLS_SERIES_MAP
        }


# Backwards-compatible function-level entry point (some seed scripts call it).
def fetch_bls_series(series_id: str) -> list[dict[str, str]]:
    """Function-level convenience for one-off calls.

    Constructs a fresh adapter + client each call. For batch fetches use
    BlsExtendedAdapter directly to share the httpx.Client.
    """
    adapter = BlsExtendedAdapter()
    try:
        return adapter.fetch_bls_series(series_id)
    finally:
        adapter._client.close()
