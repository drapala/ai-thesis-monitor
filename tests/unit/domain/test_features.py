from decimal import Decimal

from ai_thesis_monitor.domain.metrics.features import build_feature_payload


def test_build_feature_payload_computes_trend_and_acceleration() -> None:
    payload = build_feature_payload(
        series=[
            Decimal("-6.0"),
            Decimal("-10.0"),
            Decimal("-18.0"),
        ]
    )
    assert payload["trend_4w"] == "deteriorating"
    assert payload["acceleration"] == "negative"


def test_build_feature_payload_handles_empty_series() -> None:
    payload = build_feature_payload(series=[])
    assert payload["trend_4w"] == "flat"
    assert payload["acceleration"] == "flat"
    assert payload["latest"] is None


def test_build_feature_payload_steady_series_acceleration_flat() -> None:
    steady_series = [Decimal("10"), Decimal("9"), Decimal("8"), Decimal("7")]
    payload = build_feature_payload(series=steady_series)
    assert payload["trend_4w"] == "deteriorating"
    assert payload["acceleration"] == "flat"
