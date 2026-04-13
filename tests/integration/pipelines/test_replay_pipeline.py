from __future__ import annotations

from queue import Queue
from threading import Event, Thread

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session as OrmSession

from ai_thesis_monitor.cli.main import app
from ai_thesis_monitor.db.models.core import PipelineRun, Source
from ai_thesis_monitor.ingestion.pipelines.weekly import WeeklyPipelineResult
from ai_thesis_monitor.ops.replay.service import ReplayResult, replay_week

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


def test_replay_week_failure_does_not_block_retry_until_caller_rollback(db_session, monkeypatch) -> None:
    second_finished = Event()
    second_lock_attempted = Event()
    second_outcome: Queue[ReplayResult | BaseException] = Queue(maxsize=1)
    bind = db_session.get_bind()
    lock_attempts = {"count": 0}
    pipeline_attempts = {"count": 0}

    def record_lock_attempt(session, lock_id):
        lock_attempts["count"] += 1
        if lock_attempts["count"] == 2:
            second_lock_attempted.set()
        return acquire_replay_lock(session, lock_id)

    def fail_once(*, module_histories, critical_claims):
        pipeline_attempts["count"] += 1
        if pipeline_attempts["count"] == 1:
            raise RuntimeError("boom")
        return WeeklyPipelineResult(
            module_scores_written=2,
            tripwires_written=1,
            alerts_written=1,
            narratives_written=1,
        )

    from ai_thesis_monitor.ops.replay.service import _acquire_replay_lock as acquire_replay_lock

    monkeypatch.setattr("ai_thesis_monitor.ops.replay.service._acquire_replay_lock", record_lock_attempt)
    monkeypatch.setattr("ai_thesis_monitor.ops.replay.service.run_weekly_pipeline", fail_once)

    with pytest.raises(RuntimeError):
        replay_week(db_session, start_date=REPLAY_START, end_date=REPLAY_END)

    def run_second_replay() -> None:
        session = OrmSession(bind)
        try:
            result = replay_week(session, start_date=REPLAY_START, end_date=REPLAY_END)
            session.commit()
            second_outcome.put(result)
        except BaseException as exc:
            second_outcome.put(exc)
        finally:
            second_finished.set()
            session.close()

    thread = Thread(target=run_second_replay)
    thread.start()

    try:
        assert second_lock_attempted.wait(timeout=2)
        assert second_finished.wait(timeout=0.2)

        outcome = second_outcome.get_nowait()
        if isinstance(outcome, BaseException):
            raise outcome

        verifier = OrmSession(bind)
        try:
            completed_runs = verifier.scalars(
                select(PipelineRun).where(*_replay_filters(), PipelineRun.status == "completed")
            ).all()
        finally:
            verifier.close()

        assert outcome.module_scores_written == 2
        assert len(completed_runs) == 1
    finally:
        if db_session.in_transaction():
            db_session.rollback()
        thread.join(timeout=2)


def test_replay_week_fast_path_releases_lock(db_session) -> None:
    replay_week(db_session, start_date=REPLAY_START, end_date=REPLAY_END)
    second = replay_week(db_session, start_date=REPLAY_START, end_date=REPLAY_END)
    assert second.module_scores_written == 0
    assert not db_session.in_nested_transaction()


def test_replay_week_second_session_fast_paths_without_waiting_for_caller_transaction(
    db_session, monkeypatch
) -> None:
    second_finished = Event()
    second_lock_attempted = Event()
    second_outcome: Queue[ReplayResult | BaseException] = Queue(maxsize=1)
    bind = db_session.get_bind()
    original_acquire = "ai_thesis_monitor.ops.replay.service._acquire_replay_lock"
    lock_attempts = {"count": 0}
    transaction = db_session.begin()
    sentinel = Source(
        source_key="replay_window_guard",
        source_name="Replay Window Guard",
        source_type="test",
        base_url="https://example.test/window",
        config={"guard": "window"},
        reliability_score=0.84,
        active=True,
    )
    db_session.add(sentinel)
    db_session.flush()
    sentinel_id = sentinel.id

    def record_second_lock_attempt(session, lock_id):
        lock_attempts["count"] += 1
        if lock_attempts["count"] == 2:
            second_lock_attempted.set()
        return acquire_replay_lock(session, lock_id)

    from ai_thesis_monitor.ops.replay.service import _acquire_replay_lock as acquire_replay_lock

    monkeypatch.setattr(original_acquire, record_second_lock_attempt)

    first = replay_week(db_session, start_date=REPLAY_START, end_date=REPLAY_END)
    assert first.module_scores_written >= 0

    def run_second_replay() -> None:
        session = OrmSession(bind)
        try:
            result = replay_week(session, start_date=REPLAY_START, end_date=REPLAY_END)
            session.commit()
            second_outcome.put(result)
        except BaseException as exc:
            second_outcome.put(exc)
        finally:
            second_finished.set()
            session.close()

    thread = Thread(target=run_second_replay)
    thread.start()

    try:
        assert second_lock_attempted.wait(timeout=2)
        assert second_finished.wait(timeout=0.2)

        thread.join(timeout=2)
        assert not thread.is_alive()

        outcome = second_outcome.get_nowait()
        if isinstance(outcome, BaseException):
            raise outcome

        verifier = OrmSession(bind)
        try:
            completed_runs = verifier.scalars(
                select(PipelineRun).where(*_replay_filters(), PipelineRun.status == "completed")
            ).all()
            assert verifier.get(Source, sentinel_id) is None
        finally:
            verifier.close()

        assert outcome.module_scores_written == 0
        assert len(completed_runs) == 1
    finally:
        transaction.rollback()
        thread.join(timeout=2)


def test_replay_week_rejects_invalid_dates(db_session) -> None:
    with pytest.raises(ValueError):
        replay_week(db_session, start_date="not-a-date", end_date=REPLAY_END)
    assert db_session.scalar(select(func.count()).select_from(PipelineRun)) == 0

    with pytest.raises(ValueError):
        replay_week(db_session, start_date=REPLAY_END, end_date=REPLAY_START)
    assert db_session.scalar(select(func.count()).select_from(PipelineRun)) == 0


def test_replay_week_cli_invalid_window(cli_runner, db_session) -> None:
    result = cli_runner.invoke(app, ["replay-week", "invalid", REPLAY_END])
    assert result.exit_code != 0
    assert db_session.scalar(select(func.count()).select_from(PipelineRun)) == 0


def test_replay_week_preserves_outer_transaction(db_session) -> None:
    transaction = db_session.begin()
    sentinel = Source(
        source_key="replay_guard",
        source_name="Replay Guard",
        source_type="test",
        base_url="https://example.test",
        config={"guard": True},
        reliability_score=0.42,
        active=True,
    )
    db_session.add(sentinel)
    db_session.flush()
    sentinel_id = sentinel.id

    try:
        replay_week(db_session, start_date=REPLAY_START, end_date=REPLAY_END)

        other_session = OrmSession(db_session.get_bind())
        try:
            assert other_session.get(Source, sentinel_id) is None
        finally:
            other_session.close()
    finally:
        transaction.rollback()
