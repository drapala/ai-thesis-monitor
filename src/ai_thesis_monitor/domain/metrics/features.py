from decimal import Decimal
from typing import Dict, List, Union


def build_feature_payload(*, series: List[Decimal]) -> Dict[str, Union[str, Decimal, None]]:
    if not series:
        return {
            "trend_4w": "flat",
            "acceleration": "flat",
            "latest": None,
        }

    latest = series[-1]
    if len(series) == 1:
        return {
            "trend_4w": "flat",
            "acceleration": "flat",
            "latest": latest,
        }

    previous = series[-2]
    trend = "deteriorating" if latest < previous else "improving"
    delta_latest = latest - previous
    if len(series) >= 3:
        delta_previous = previous - series[-3]
    else:
        delta_previous = delta_latest

    if len(series) < 3 or delta_latest == delta_previous:
        acceleration = "flat"
    else:
        acceleration = "negative" if delta_latest < delta_previous else "positive"

    return {"latest": latest, "trend_4w": trend, "acceleration": acceleration}
