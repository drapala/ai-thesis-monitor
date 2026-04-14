import subprocess
import sys
from contextlib import contextmanager
from datetime import date

from ai_thesis_monitor import __version__
from typer.testing import CliRunner


def test_version_command_prints_expected_value():
    from ai_thesis_monitor.cli.main import app  # imported inside to avoid hard dependency before module exists

    result = CliRunner().invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout == f"{__version__}\n"


def test_root_invocation_prints_help():
    from ai_thesis_monitor.cli.main import app

    result = CliRunner().invoke(app, [])
    assert result.exit_code == 0
    assert "Usage: ai-thesis-monitor" in result.stdout


def test_module_entrypoint_proxy_runs_version_command():
    result = subprocess.run(
        [sys.executable, "-m", "ai_thesis_monitor.cli.main", "version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout == f"{__version__}\n"


def test_run_daily_invokes_runtime_pipelines(monkeypatch):
    from ai_thesis_monitor.cli.main import app
    from ai_thesis_monitor.ingestion.pipelines.features import FeaturePipelineResult
    from ai_thesis_monitor.ingestion.pipelines.structured import StructuredPipelineResult
    from ai_thesis_monitor.ingestion.pipelines.text import TextPipelineResult

    calls: dict[str, object] = {}

    class DummySession:
        def commit(self) -> None:
            calls["commit"] = True

    dummy_session = DummySession()

    @contextmanager
    def fake_session_scope():
        yield dummy_session

    class DummyClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("ai_thesis_monitor.cli.main.build_session_factory", lambda settings: fake_session_scope)
    monkeypatch.setattr(
        "ai_thesis_monitor.cli.main._active_structured_metric_keys",
        lambda session: ["labor_productivity_yoy", "unemployment_rate_professional_services"],
    )
    monkeypatch.setattr(
        "ai_thesis_monitor.cli.main._active_text_source_keys",
        lambda session: ["rss_macro", "rss_corporate_ir"],
    )

    def fake_structured(session, *, client, metric_keys):
        calls["structured"] = (session, metric_keys)
        return StructuredPipelineResult(raw_observations=2, normalized_metrics=2)

    def fake_text(session, *, client, source_keys):
        calls["text"] = (session, source_keys)
        return TextPipelineResult(raw_observations=3, claims_created=1)

    def fake_features(session, *, metric_keys=None, observed_date_lte=None):
        calls["features"] = (session, metric_keys, observed_date_lte)
        return FeaturePipelineResult(metric_features_written=2)

    monkeypatch.setattr("ai_thesis_monitor.cli.main.run_structured_pipeline", fake_structured)
    monkeypatch.setattr("ai_thesis_monitor.cli.main.run_text_pipeline", fake_text)
    monkeypatch.setattr("ai_thesis_monitor.cli.main.run_feature_pipeline", fake_features)
    monkeypatch.setattr("ai_thesis_monitor.cli.main.httpx.Client", DummyClient)

    result = CliRunner().invoke(app, ["run-daily"])

    assert result.exit_code == 0
    assert "daily pipeline completed" in result.stdout
    assert calls["structured"] == (
        dummy_session,
        ["labor_productivity_yoy", "unemployment_rate_professional_services"],
    )
    assert calls["text"] == (dummy_session, ["rss_macro", "rss_corporate_ir"])
    assert calls["features"] == (dummy_session, None, None)
    assert calls["commit"] is True


def test_run_weekly_accepts_explicit_score_date(monkeypatch):
    from ai_thesis_monitor.cli.main import app
    from ai_thesis_monitor.ingestion.pipelines.weekly import WeeklyPipelineResult

    calls: dict[str, object] = {}

    class DummySession:
        def commit(self) -> None:
            calls["commit"] = True

    dummy_session = DummySession()

    @contextmanager
    def fake_session_scope():
        yield dummy_session

    monkeypatch.setattr("ai_thesis_monitor.cli.main.build_session_factory", lambda settings: fake_session_scope)

    def fake_weekly(*, session, score_date):
        calls["weekly"] = (session, score_date)
        return WeeklyPipelineResult(
            module_scores_written=2,
            tripwires_written=1,
            alerts_written=1,
            narratives_written=1,
        )

    monkeypatch.setattr("ai_thesis_monitor.cli.main.run_weekly_pipeline", fake_weekly)

    result = CliRunner().invoke(app, ["run-weekly", "2026-04-13"])

    assert result.exit_code == 0
    assert "weekly pipeline completed" in result.stdout
    assert calls["weekly"] == (dummy_session, date(2026, 4, 13))
    assert calls["commit"] is True
