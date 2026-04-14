from __future__ import annotations

from copy import deepcopy

import pytest
from sqlalchemy import delete, select
from typer.testing import CliRunner

from ai_thesis_monitor.cli.main import app
from ai_thesis_monitor.db.models.core import MetricDefinition, Source

EXPECTED_SOURCE_CONTRACT: dict[str, dict] = {
    "fred": {
        "source_name": "Federal Reserve Economic Data",
        "source_type": "structured_csv",
        "base_url": "https://fred.stlouisfed.org",
        "config": {"path": "/graph/fredgraph.csv"},
        "reliability_score": 0.95,
        "active": True,
    },
    "rss_macro": {
        "source_name": "Macro RSS Feed",
        "source_type": "rss",
        "base_url": "https://feeds.feedburner.com/CalculatedRisk",
        "config": {"kind": "macro"},
        "reliability_score": 0.85,
        "active": True,
    },
    "rss_corporate_ir": {
        "source_name": "AI Claims RSS Feed",
        "source_type": "rss",
        "base_url": (
            "https://news.google.com/rss/search?q=%28AI%20layoffs%29%20OR%20"
            "%28reduce%20workforce%20AI%29%20OR%20%28SaaS%20pricing%20discounts%29%20OR%20"
            "%28AI%20build%20vs%20buy%29&hl=en-US&gl=US&ceid=US:en"
        ),
        "config": {"kind": "ai_claims"},
        "reliability_score": 0.82,
        "active": True,
    },
}

EXPECTED_METRIC_CONTRACT: dict[str, dict] = {
    "ai_adoption_work_total": {
        "module_key": "diffusion",
        "name": "AI adoption at work",
        "description": "Share of workers reporting AI use at work",
        "frequency": "monthly",
        "unit": "share",
        "lag_category": "confirmatory",
        "weight": 1.20,
        "expected_direction_citadel": "up",
        "expected_direction_citrini": "up",
        "primary_feature_key": "level",
        "signal_transform": "adoption_only",
        "min_history_points": 1,
        "is_leading": True,
        "config": {"manual": True},
    },
    "ai_adoption_work_daily": {
        "module_key": "diffusion",
        "name": "Daily AI use",
        "description": "Share of workers using AI daily",
        "frequency": "monthly",
        "unit": "share",
        "lag_category": "leading",
        "weight": 1.00,
        "expected_direction_citadel": "up",
        "expected_direction_citrini": "up",
        "primary_feature_key": "level",
        "signal_transform": "adoption_only",
        "min_history_points": 1,
        "is_leading": True,
        "config": {"manual": True},
    },
    "hours_saved_per_week_ai_users": {
        "module_key": "diffusion",
        "name": "Hours saved by AI users",
        "description": "Weekly hours saved reported by AI users",
        "frequency": "monthly",
        "unit": "hours",
        "lag_category": "leading",
        "weight": 0.90,
        "expected_direction_citadel": "up",
        "expected_direction_citrini": "up",
        "primary_feature_key": "level",
        "signal_transform": "adoption_only",
        "min_history_points": 1,
        "is_leading": True,
        "config": {"manual": True},
    },
    "labor_productivity_yoy": {
        "module_key": "productivity",
        "name": "Labor productivity YoY",
        "description": "US labor productivity annual growth",
        "frequency": "quarterly",
        "unit": "percent",
        "lag_category": "confirmatory",
        "weight": 1.20,
        "expected_direction_citadel": "up",
        "expected_direction_citrini": "up",
        "primary_feature_key": "yoy",
        "signal_transform": "higher_is_citadel",
        "min_history_points": 4,
        "is_leading": False,
        "config": {"source_key": "fred", "series_id": "OPHNFB"},
    },
    "revenue_per_employee_large_tech": {
        "module_key": "productivity",
        "name": "Revenue per employee",
        "description": "Large tech revenue per employee",
        "frequency": "quarterly",
        "unit": "usd",
        "lag_category": "confirmatory",
        "weight": 0.80,
        "expected_direction_citadel": "up",
        "expected_direction_citrini": "up",
        "primary_feature_key": "yoy",
        "signal_transform": "higher_is_citadel",
        "min_history_points": 4,
        "is_leading": False,
        "config": {"manual": True},
    },
    "software_postings_yoy": {
        "module_key": "labor",
        "name": "Software postings YoY",
        "description": "Software job postings year-over-year",
        "frequency": "weekly",
        "unit": "percent",
        "lag_category": "leading",
        "weight": 1.30,
        "expected_direction_citadel": "up",
        "expected_direction_citrini": "down",
        "primary_feature_key": "yoy",
        "signal_transform": "lower_is_citrini",
        "min_history_points": 8,
        "is_leading": True,
        "config": {"manual": True},
    },
    "pm_postings_yoy": {
        "module_key": "labor",
        "name": "PM postings YoY",
        "description": "Product management job postings year-over-year",
        "frequency": "weekly",
        "unit": "percent",
        "lag_category": "leading",
        "weight": 1.10,
        "expected_direction_citadel": "up",
        "expected_direction_citrini": "down",
        "primary_feature_key": "yoy",
        "signal_transform": "lower_is_citrini",
        "min_history_points": 8,
        "is_leading": True,
        "config": {"manual": True},
    },
    "finance_ops_postings_yoy": {
        "module_key": "labor",
        "name": "Finance and ops postings YoY",
        "description": "Finance and ops job postings year-over-year",
        "frequency": "weekly",
        "unit": "percent",
        "lag_category": "leading",
        "weight": 1.00,
        "expected_direction_citadel": "up",
        "expected_direction_citrini": "down",
        "primary_feature_key": "yoy",
        "signal_transform": "lower_is_citrini",
        "min_history_points": 8,
        "is_leading": True,
        "config": {"manual": True},
    },
    "layoffs_white_collar_count": {
        "module_key": "labor",
        "name": "White-collar layoff count",
        "description": "Count of public white-collar layoff events",
        "frequency": "weekly",
        "unit": "count",
        "lag_category": "leading",
        "weight": 1.25,
        "expected_direction_citadel": "down",
        "expected_direction_citrini": "up",
        "primary_feature_key": "level",
        "signal_transform": "higher_is_citrini",
        "min_history_points": 4,
        "is_leading": True,
        "config": {"source_key": "rss_corporate_ir"},
    },
    "unemployment_rate_professional_services": {
        "module_key": "labor",
        "name": "Unemployment professional services",
        "description": "Unemployment rate in professional services",
        "frequency": "monthly",
        "unit": "percent",
        "lag_category": "confirmatory",
        "weight": 1.10,
        "expected_direction_citadel": "down",
        "expected_direction_citrini": "up",
        "primary_feature_key": "level",
        "signal_transform": "higher_is_citrini",
        "min_history_points": 6,
        "is_leading": False,
        "config": {"source_key": "fred", "series_id": "UNRATE"},
    },
    "discretionary_spending_high_income": {
        "module_key": "demand",
        "name": "Discretionary spending high income",
        "description": "High-income discretionary spending proxy",
        "frequency": "monthly",
        "unit": "index",
        "lag_category": "confirmatory",
        "weight": 1.20,
        "expected_direction_citadel": "up",
        "expected_direction_citrini": "down",
        "primary_feature_key": "yoy",
        "signal_transform": "lower_is_citrini",
        "min_history_points": 6,
        "is_leading": False,
        "config": {"manual": True},
    },
    "restaurant_spending_high_income": {
        "module_key": "demand",
        "name": "Restaurant spending high income",
        "description": "High-income restaurant spending proxy",
        "frequency": "weekly",
        "unit": "index",
        "lag_category": "leading",
        "weight": 0.90,
        "expected_direction_citadel": "up",
        "expected_direction_citrini": "down",
        "primary_feature_key": "trend_4w",
        "signal_transform": "lower_is_citrini",
        "min_history_points": 4,
        "is_leading": True,
        "config": {"manual": True},
    },
    "travel_spending_high_income": {
        "module_key": "demand",
        "name": "Travel spending high income",
        "description": "High-income travel spending proxy",
        "frequency": "weekly",
        "unit": "index",
        "lag_category": "leading",
        "weight": 0.90,
        "expected_direction_citadel": "up",
        "expected_direction_citrini": "down",
        "primary_feature_key": "trend_4w",
        "signal_transform": "lower_is_citrini",
        "min_history_points": 4,
        "is_leading": True,
        "config": {"manual": True},
    },
    "savings_rate_high_income": {
        "module_key": "demand",
        "name": "Savings rate high income",
        "description": "High-income savings rate proxy",
        "frequency": "monthly",
        "unit": "percent",
        "lag_category": "confirmatory",
        "weight": 0.80,
        "expected_direction_citadel": "neutral",
        "expected_direction_citrini": "up",
        "primary_feature_key": "yoy",
        "signal_transform": "higher_is_citrini",
        "min_history_points": 6,
        "is_leading": False,
        "config": {"manual": True},
    },
    "saas_renewal_discount_mentions": {
        "module_key": "intermediation",
        "name": "SaaS renewal discount mentions",
        "description": "Textual mentions of renewal pressure",
        "frequency": "weekly",
        "unit": "count",
        "lag_category": "leading",
        "weight": 1.10,
        "expected_direction_citadel": "down",
        "expected_direction_citrini": "up",
        "primary_feature_key": "count_4w",
        "signal_transform": "higher_is_citrini",
        "min_history_points": 2,
        "is_leading": True,
        "config": {"source_key": "rss_corporate_ir"},
    },
    "ai_build_vs_buy_mentions": {
        "module_key": "intermediation",
        "name": "Build vs buy mentions",
        "description": "Textual mentions of AI build-vs-buy substitution",
        "frequency": "weekly",
        "unit": "count",
        "lag_category": "leading",
        "weight": 1.00,
        "expected_direction_citadel": "down",
        "expected_direction_citrini": "up",
        "primary_feature_key": "count_4w",
        "signal_transform": "higher_is_citrini",
        "min_history_points": 2,
        "is_leading": True,
        "config": {"source_key": "rss_corporate_ir"},
    },
    "card_interchange_pressure_mentions": {
        "module_key": "intermediation",
        "name": "Interchange pressure mentions",
        "description": "Textual mentions of interchange or pricing pressure",
        "frequency": "weekly",
        "unit": "count",
        "lag_category": "leading",
        "weight": 0.90,
        "expected_direction_citadel": "down",
        "expected_direction_citrini": "up",
        "primary_feature_key": "count_4w",
        "signal_transform": "higher_is_citrini",
        "min_history_points": 2,
        "is_leading": True,
        "config": {"source_key": "rss_macro"},
    },
    "marketplace_take_rate_pressure_mentions": {
        "module_key": "intermediation",
        "name": "Marketplace take-rate pressure mentions",
        "description": "Textual mentions of marketplace take-rate pressure",
        "frequency": "weekly",
        "unit": "count",
        "lag_category": "leading",
        "weight": 0.90,
        "expected_direction_citadel": "down",
        "expected_direction_citrini": "up",
        "primary_feature_key": "count_4w",
        "signal_transform": "higher_is_citrini",
        "min_history_points": 2,
        "is_leading": True,
        "config": {"source_key": "rss_macro"},
    },
    "prime_mortgage_delinquency_tech_metros": {
        "module_key": "credit_housing",
        "name": "Prime mortgage delinquency tech metros",
        "description": "Prime delinquency rate in tech-heavy metros",
        "frequency": "monthly",
        "unit": "percent",
        "lag_category": "confirmatory",
        "weight": 1.20,
        "expected_direction_citadel": "down",
        "expected_direction_citrini": "up",
        "primary_feature_key": "yoy",
        "signal_transform": "higher_is_citrini",
        "min_history_points": 6,
        "is_leading": False,
        "config": {"manual": True},
    },
    "heloc_draws_tech_metros": {
        "module_key": "credit_housing",
        "name": "HELOC draws tech metros",
        "description": "HELOC draws in tech-heavy metros",
        "frequency": "monthly",
        "unit": "usd",
        "lag_category": "confirmatory",
        "weight": 0.90,
        "expected_direction_citadel": "down",
        "expected_direction_citrini": "up",
        "primary_feature_key": "yoy",
        "signal_transform": "higher_is_citrini",
        "min_history_points": 6,
        "is_leading": False,
        "config": {"manual": True},
    },
    "home_price_yoy_sf": {
        "module_key": "credit_housing",
        "name": "SF home prices YoY",
        "description": "San Francisco home price growth",
        "frequency": "monthly",
        "unit": "percent",
        "lag_category": "confirmatory",
        "weight": 0.80,
        "expected_direction_citadel": "up",
        "expected_direction_citrini": "down",
        "primary_feature_key": "yoy",
        "signal_transform": "lower_is_citrini",
        "min_history_points": 6,
        "is_leading": False,
        "config": {"manual": True},
    },
    "home_price_yoy_seattle": {
        "module_key": "credit_housing",
        "name": "Seattle home prices YoY",
        "description": "Seattle home price growth",
        "frequency": "monthly",
        "unit": "percent",
        "lag_category": "confirmatory",
        "weight": 0.80,
        "expected_direction_citadel": "up",
        "expected_direction_citrini": "down",
        "primary_feature_key": "yoy",
        "signal_transform": "lower_is_citrini",
        "min_history_points": 6,
        "is_leading": False,
        "config": {"manual": True},
    },
    "revolving_balance_high_income": {
        "module_key": "credit_housing",
        "name": "Revolving balance high income",
        "description": "High-income revolving credit proxy",
        "frequency": "monthly",
        "unit": "usd",
        "lag_category": "confirmatory",
        "weight": 0.90,
        "expected_direction_citadel": "down",
        "expected_direction_citrini": "up",
        "primary_feature_key": "yoy",
        "signal_transform": "higher_is_citrini",
        "min_history_points": 6,
        "is_leading": False,
        "config": {"manual": True},
    },
}


@pytest.fixture(autouse=True)
def clean_reference_tables(db_session) -> None:
    db_session.execute(delete(MetricDefinition))
    db_session.execute(delete(Source))
    db_session.commit()
    yield
    db_session.execute(delete(MetricDefinition))
    db_session.execute(delete(Source))
    db_session.commit()


def test_seed_reference_data_populates_required_sources_and_metrics(
    cli_runner: CliRunner, db_session
) -> None:
    assert db_session.scalar(select(Source.id).limit(1)) is None
    assert db_session.scalar(select(MetricDefinition.id).limit(1)) is None

    result = cli_runner.invoke(app, ["seed-reference-data"])
    assert result.exit_code == 0

    sources = {
        source.source_key: source
        for source in db_session.scalars(select(Source)).all()
    }
    assert set(EXPECTED_SOURCE_CONTRACT) <= set(sources)
    for source_key, expected in EXPECTED_SOURCE_CONTRACT.items():
        source = sources[source_key]
        assert source.source_name == expected["source_name"]
        assert source.source_type == expected["source_type"]
        assert source.base_url == expected["base_url"]
        assert source.config == expected["config"]
        assert source.reliability_score == expected["reliability_score"]
        assert source.active == expected["active"]

    metric_keys = set(db_session.scalars(select(MetricDefinition.metric_key)))
    assert {
        "ai_adoption_work_total",
        "labor_productivity_yoy",
        "software_postings_yoy",
        "discretionary_spending_high_income",
        "saas_renewal_discount_mentions",
        "prime_mortgage_delinquency_tech_metros",
    }.issubset(metric_keys)


def test_seed_reference_data_updates_stale_reference_rows(
    cli_runner: CliRunner, db_session
) -> None:
    stale_source = Source(
        source_key="rss_macro",
        source_name="Old Source Name",
        source_type="rss",
        base_url="https://example.com/stale.xml",
        config={"kind": "stale"},
        reliability_score=0.10,
        active=False,
    )
    stale_metric_payload = deepcopy(EXPECTED_METRIC_CONTRACT["saas_renewal_discount_mentions"])
    stale_metric_payload.update(
        {
            "metric_key": "saas_renewal_discount_mentions",
            "module_key": "wrong_module",
            "name": "Old Metric Name",
            "description": "stale",
            "frequency": "monthly",
            "unit": "index",
            "lag_category": "confirmatory",
            "weight": 9.99,
            "expected_direction_citadel": "up",
            "expected_direction_citrini": "down",
            "primary_feature_key": "old_feature",
            "signal_transform": "old_transform",
            "min_history_points": 99,
            "is_leading": False,
            "config": {"manual": True},
            "is_active": True,
        }
    )
    stale_metric = MetricDefinition(**stale_metric_payload)

    db_session.add(stale_source)
    db_session.add(stale_metric)
    db_session.commit()

    result = cli_runner.invoke(app, ["seed-reference-data"])
    assert result.exit_code == 0

    db_session.expire_all()

    source = db_session.scalar(select(Source).where(Source.source_key == "rss_macro"))
    assert source is not None
    expected_source = EXPECTED_SOURCE_CONTRACT["rss_macro"]
    assert source.source_name == expected_source["source_name"]
    assert source.source_type == expected_source["source_type"]
    assert source.base_url == expected_source["base_url"]
    assert source.config == expected_source["config"]
    assert source.reliability_score == expected_source["reliability_score"]
    assert source.active == expected_source["active"]

    metric = db_session.scalar(
        select(MetricDefinition).where(MetricDefinition.metric_key == "saas_renewal_discount_mentions")
    )
    assert metric is not None
    expected_metric = EXPECTED_METRIC_CONTRACT["saas_renewal_discount_mentions"]
    assert metric.module_key == expected_metric["module_key"]
    assert metric.name == expected_metric["name"]
    assert metric.description == expected_metric["description"]
    assert metric.frequency == expected_metric["frequency"]
    assert metric.unit == expected_metric["unit"]
    assert metric.lag_category == expected_metric["lag_category"]
    assert metric.weight == expected_metric["weight"]
    assert metric.expected_direction_citadel == expected_metric["expected_direction_citadel"]
    assert metric.expected_direction_citrini == expected_metric["expected_direction_citrini"]
    assert metric.primary_feature_key == expected_metric["primary_feature_key"]
    assert metric.signal_transform == expected_metric["signal_transform"]
    assert metric.min_history_points == expected_metric["min_history_points"]
    assert metric.is_leading == expected_metric["is_leading"]
    assert metric.config == expected_metric["config"]


def test_seed_reference_data_matches_approved_metric_contract(
    cli_runner: CliRunner, db_session
) -> None:
    result = cli_runner.invoke(app, ["seed-reference-data"])
    assert result.exit_code == 0

    metrics_by_key = {
        metric.metric_key: metric
        for metric in db_session.scalars(select(MetricDefinition)).all()
    }
    assert set(EXPECTED_METRIC_CONTRACT) <= set(metrics_by_key)

    for metric_key, expected in EXPECTED_METRIC_CONTRACT.items():
        metric = metrics_by_key[metric_key]
        assert metric.module_key == expected["module_key"]
        assert metric.name == expected["name"]
        assert metric.description == expected["description"]
        assert metric.frequency == expected["frequency"]
        assert metric.unit == expected["unit"]
        assert metric.lag_category == expected["lag_category"]
        assert metric.weight == expected["weight"]
        assert metric.expected_direction_citadel == expected["expected_direction_citadel"]
        assert metric.expected_direction_citrini == expected["expected_direction_citrini"]
        assert metric.primary_feature_key == expected["primary_feature_key"]
        assert metric.signal_transform == expected["signal_transform"]
        assert metric.min_history_points == expected["min_history_points"]
        assert metric.is_leading == expected["is_leading"]
        assert metric.config == expected["config"]
