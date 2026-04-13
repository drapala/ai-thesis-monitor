from decimal import Decimal
from typing import Dict, List, Union


def build_feature_payload(*, series: List[Decimal]) -> Dict[str, Union[str, Decimal]]:
    if len(series) < 2:
        return {
            "trend_4w": "flat",
            "acceleration": "flat",
            "latest": series[-1],
        }

    latest = series[-1]
    previous = series[-2]
    earliest = series[0]
    trend = "deteriorating" if latest < previous else "improving"
    acceleration = "negative" if (latest - previous) < (previous - earliest) else "positive"

    return {"latest": latest, "trend_4w": trend, "acceleration": acceleration}
