"""BLS extended adapter — Employment Cost Index (ECI) and adjacent series.

STATUS: stub. Wraps FRED for additional BLS-published series IDs that the
existing fred.py adapter does not target. No business logic yet.

Series IDs of interest (FRED hosts BLS data, fetchable as CSV):
- CIU2020000000000A — ECI civilian workers, professional/management occupations,
  benefits + wages, YoY percent change
- CIU2010000000000A — ECI civilian workers, all occupations
- LNS14000003       — Unemployment rate, professional services
- JTS1000HIL        — JOLTS Hires, Information sector (proxy for IT hiring)
- JTS5000QUL        — JOLTS Quits, Professional and Business Services

Why a separate file from fred.py:
- fred.py is generic CSV adapter; this file documents which BLS-specific series
  matter for the citadel-vs-citrini analysis and bundles them as a unit.
- Allows seed-bls-eci-data CLI command to be added later without polluting
  the generic adapter.

To implement:
1. Inherit / wrap the existing FredAdapter class (see fred.py).
2. Provide a fetch_bls_series(series_id) method that returns parsed dated points.
3. Wire to a CLI command `seed-bls-extended-data` mirroring `seed-india-it-data`.
4. Insert into expanded_proxy_data.py via upsert pattern.

Cost: free (FRED is public).
"""

from __future__ import annotations


# Series ID → (metric_key, frequency, units, transform_to_yoy)
BLS_SERIES_MAP: dict[str, dict] = {
    "CIU2020000000000A": {
        "metric_key": "eci_white_collar_yoy",
        "frequency": "quarterly",
        "units": "percent",
        "is_yoy": True,
        "description": (
            "Employment Cost Index, civilian workers, professional and related "
            "occupations, total compensation. Released quarterly, end of month "
            "following quarter close."
        ),
    },
    # Additional series ready to wire when the metric is added:
    # "CIU2010000000000A": {...},  # All civilian workers
    # "LNS14000003":      {...},  # Unemployment professional services
    # "JTS1000HIL":       {...},  # JOLTS Hires, Information
    # "JTS5000QUL":       {...},  # JOLTS Quits, Professional services
}


def fetch_bls_series(series_id: str) -> list[dict]:
    """Fetch a BLS series via FRED CSV endpoint.

    Returns a list of {date, value} dicts. NOT YET IMPLEMENTED.

    Implementation sketch (when ready):
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        # use httpx via the fred adapter pattern
        # parse CSV; coerce types; return list[{date, value}]
    """
    raise NotImplementedError(
        "bls_extended adapter is a stub. See file docstring + NEXT-ACTIONS.md "
        "for implementation steps. FredAdapter in fred.py is the working "
        "starting point — wrap it with the BLS_SERIES_MAP above."
    )
