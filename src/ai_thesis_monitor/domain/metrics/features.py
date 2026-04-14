from __future__ import annotations

import math
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Union


FeaturePayload = Dict[str, Union[str, int, Decimal, None]]
SerializedFeaturePayload = Dict[str, Union[str, int, None]]

THREE_DECIMALS = Decimal("0.001")
ZERO = Decimal("0.000")
ONE = Decimal("1.000")


def build_feature_payload(*, series: List[Decimal], frequency: str = "weekly") -> FeaturePayload:
    if not series:
        return {
            "history_points": 0,
            "latest": None,
            "value": None,
            "level": None,
            "level_signal": None,
            "yoy": None,
            "yoy_signal": None,
            "count_4w": ZERO,
            "count_4w_signal": ZERO,
            "trend_4w": "flat",
            "trend_4w_signal": ZERO,
            "acceleration": "flat",
        }

    latest = _quantize(series[-1])
    payload: FeaturePayload = {
        "history_points": len(series),
        "latest": latest,
        "value": latest,
        "level": ZERO,
        "level_signal": ZERO,
        "yoy": None,
        "yoy_signal": None,
        "count_4w": _quantize(sum(series[-4:], start=Decimal("0"))),
        "count_4w_signal": _cap_signal(abs(sum(series[-4:], start=Decimal("0"))) / Decimal("4")),
        "trend_4w": "flat",
        "trend_4w_signal": ZERO,
        "acceleration": "flat",
    }

    if len(series) > 1:
        previous = series[-2]
        prior_window = series[-5:-1] if len(series) >= 5 else series[:-1]
        prior_average = _mean(prior_window)
        if latest > prior_average:
            payload["trend_4w"] = "improving"
            payload["trend_4w_signal"] = ONE
        elif latest < prior_average:
            payload["trend_4w"] = "deteriorating"
            payload["trend_4w_signal"] = ONE

        delta_latest = latest - previous
        delta_previous = previous - series[-3] if len(series) >= 3 else delta_latest
        if len(series) >= 3:
            if delta_latest > delta_previous:
                payload["acceleration"] = "positive"
            elif delta_latest < delta_previous:
                payload["acceleration"] = "negative"

        baseline_window = series[-13:-1] if len(series) >= 13 else series[:-1]
        if baseline_window:
            level = _baseline_zscore(latest, baseline_window)
            payload["level"] = _quantize(level)
            payload["level_signal"] = _cap_signal(abs(level) / Decimal("2"))

    seasonal_lag = _seasonal_lag(frequency)
    if seasonal_lag is not None and len(series) > seasonal_lag:
        previous_period = series[-(seasonal_lag + 1)]
        if previous_period != 0:
            yoy = (latest - previous_period) / abs(previous_period)
            payload["yoy"] = _quantize(yoy)
            payload["yoy_signal"] = _cap_signal(abs(yoy) / Decimal("0.10"))

    return payload


def serialize_feature_payload(payload: FeaturePayload) -> SerializedFeaturePayload:
    serialized: SerializedFeaturePayload = {}
    for key, value in payload.items():
        if isinstance(value, Decimal):
            serialized[key] = f"{value:.3f}"
        else:
            serialized[key] = value
    return serialized


def _seasonal_lag(frequency: str) -> int | None:
    if frequency == "weekly":
        return 52
    if frequency == "monthly":
        return 12
    if frequency == "quarterly":
        return 4
    return None


def _baseline_zscore(latest: Decimal, baseline_window: List[Decimal]) -> Decimal:
    baseline_mean = _mean(baseline_window)
    variance = _mean([(point - baseline_mean) ** 2 for point in baseline_window])
    if variance == 0:
        if latest == baseline_mean:
            return ZERO
        return ONE if latest > baseline_mean else -ONE

    standard_deviation = Decimal(str(math.sqrt(float(variance))))
    if standard_deviation == 0:
        return ZERO
    return (latest - baseline_mean) / standard_deviation


def _mean(values: List[Decimal]) -> Decimal:
    if not values:
        return ZERO
    return sum(values, start=Decimal("0")) / Decimal(len(values))


def _cap_signal(value: Decimal) -> Decimal:
    if value <= 0:
        return ZERO
    return _quantize(min(value, ONE))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(THREE_DECIMALS, rounding=ROUND_HALF_UP)
