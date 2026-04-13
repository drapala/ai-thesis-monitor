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
