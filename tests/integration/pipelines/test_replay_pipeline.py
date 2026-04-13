from __future__ import annotations

import pytest
from sqlalchemy import delete, func, select

from ai_thesis_monitor.cli.main import app
from ai_thesis_monitor.db.models.core import PipelineRun
from ai_thesis_monitor.ops.replay.service import replay_week

REPLAY_START = "2026-03-30"
REPLAY_END = "2026-04-06"


def _replay_filters(start_date: str = REPLAY_START, end_date: str = REPLAY_END):
    inputs_start = PipelineRun.inputs.op("->>")("start_date")
    inputs_end = PipelineRun.inputs.op("->>")("end_date")
    return (
        PipelineRun.run_type == "replay_week",
        inputs_start == start_date,
        inputs_end == end_date,
    )


@pytest.fixture(autouse=True)
def clear_pipeline_runs(db_session) -> None:
    db_session.execute(delete(PipelineRun))
    db_session.commit()
    yield
    db_session.execute(delete(PipelineRun))
    db_session.commit()


def test_replay_week_is_idempotent(db_session) -> None:
    first = replay_week(db_session, start_date=REPLAY_START, end_date=REPLAY_END)
    assert first.module_scores_written >= 0

    count = db_session.scalar(select(func.count()).select_from(PipelineRun))
    assert count == 1

    run = db_session.scalar(select(PipelineRun).where(*_replay_filters()))
    assert run is not None
    assert run.status == "completed"
    assert run.outputs_summary.get("mode") == "replay"

    second = replay_week(db_session, start_date=REPLAY_START, end_date=REPLAY_END)
    assert second.module_scores_written == 0
    assert db_session.scalar(select(func.count()).select_from(PipelineRun)) == 1


def test_replay_week_cli_records_run(cli_runner, db_session) -> None:
    result = cli_runner.invoke(app, ["replay-week", REPLAY_START, REPLAY_END])
    assert result.exit_code == 0
    assert "replayed 2026-03-30 to 2026-04-06" in result.stdout

    row = db_session.scalar(select(PipelineRun).where(*_replay_filters()))
    assert row is not None
    assert row.status == "completed"


def test_replay_week_rolls_back_on_failure(db_session, monkeypatch) -> None:
    def fail(*, module_histories, critical_claims):
        raise RuntimeError("boom")

    monkeypatch.setattr("ai_thesis_monitor.ops.replay.service.run_weekly_pipeline", fail)

    with pytest.raises(RuntimeError):
        replay_week(db_session, start_date=REPLAY_START, end_date=REPLAY_END)

    db_session.expire_all()
    assert db_session.scalar(select(func.count()).select_from(PipelineRun)) == 0
