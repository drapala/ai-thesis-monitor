from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from queue import Queue
from threading import Event, Thread

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session as OrmSession

from ai_thesis_monitor.db.models.analytics import (
    Alert,
    Claim,
    MetricFeature,
    ModuleScore,
    NarrativeSnapshot,
    NormalizedMetric,
    ScoreEvidence,
    TripwireEvent,
)
from ai_thesis_monitor.cli.main import app
from ai_thesis_monitor.db.models.core import (
    Document,
    DocumentChunk,
    MetricDefinition,
    PipelineRun,
    RawObservation,
    Source,
)
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


def _replay_score_date_filters(score_date: str = REPLAY_END):
    inputs_end = PipelineRun.inputs.op("->>")("end_date")
    return (
        PipelineRun.run_type == "replay_week",
        PipelineRun.status == "completed",
        inputs_end == score_date,
    )


@pytest.fixture(autouse=True)
def clear_pipeline_runs(db_session) -> None:
    db_session.execute(delete(Alert))
    db_session.execute(delete(TripwireEvent))
    db_session.execute(delete(NarrativeSnapshot))
    db_session.execute(delete(ModuleScore))
    db_session.execute(delete(ScoreEvidence))
    db_session.execute(delete(Claim))
    db_session.execute(delete(DocumentChunk))
    db_session.execute(delete(Document))
    db_session.execute(delete(MetricFeature))
    db_session.execute(delete(NormalizedMetric))
    db_session.execute(delete(RawObservation))
    db_session.execute(delete(MetricDefinition))
    db_session.execute(delete(PipelineRun))
    db_session.execute(delete(Source))
    db_session.commit()
    yield
    db_session.execute(delete(Alert))
    db_session.execute(delete(TripwireEvent))
    db_session.execute(delete(NarrativeSnapshot))
    db_session.execute(delete(ModuleScore))
    db_session.execute(delete(ScoreEvidence))
    db_session.execute(delete(Claim))
    db_session.execute(delete(DocumentChunk))
    db_session.execute(delete(Document))
    db_session.execute(delete(MetricFeature))
    db_session.execute(delete(NormalizedMetric))
    db_session.execute(delete(RawObservation))
    db_session.execute(delete(MetricDefinition))
    db_session.execute(delete(PipelineRun))
    db_session.execute(delete(Source))
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


def test_replay_week_materializes_outputs_for_end_date(db_session) -> None:
    score_date = date.fromisoformat(REPLAY_END)
    _seed_weekly_inputs(db_session, score_date=score_date)

    result = replay_week(db_session, start_date=REPLAY_START, end_date=REPLAY_END)

    assert result.module_scores_written == 1
    assert result.tripwires_written == 1
    assert result.alerts_written == 1
    assert result.narratives_written == 1

    module_score = db_session.scalar(select(ModuleScore))
    assert module_score is not None
    assert module_score.score_date == score_date

    tripwire = db_session.scalar(select(TripwireEvent))
    assert tripwire is not None
    assert tripwire.event_date == score_date

    narrative = db_session.scalar(select(NarrativeSnapshot))
    assert narrative is not None
    assert narrative.snapshot_date == score_date

    hardcoded_date = date(2026, 4, 13)
    assert db_session.scalar(
        select(func.count()).select_from(ModuleScore).where(ModuleScore.score_date == hardcoded_date)
    ) == 0
    assert db_session.scalar(
        select(func.count()).select_from(TripwireEvent).where(TripwireEvent.event_date == hardcoded_date)
    ) == 0
    assert db_session.scalar(
        select(func.count()).select_from(NarrativeSnapshot).where(NarrativeSnapshot.snapshot_date == hardcoded_date)
    ) == 0


def test_replay_week_fast_paths_same_score_date_even_with_different_start_date(db_session) -> None:
    score_date = date.fromisoformat(REPLAY_END)
    _seed_weekly_inputs(db_session, score_date=score_date)

    first = replay_week(db_session, start_date=REPLAY_START, end_date=REPLAY_END)
    db_session.commit()

    second = replay_week(db_session, start_date="2026-03-29", end_date=REPLAY_END)
    db_session.commit()

    assert first.module_scores_written == 1
    assert second == ReplayResult(0, 0, 0, 0)
    assert db_session.scalar(select(func.count()).select_from(PipelineRun)) == 1
    assert db_session.scalar(select(func.count()).select_from(ModuleScore)) == 1
    assert db_session.scalar(select(func.count()).select_from(ScoreEvidence)) == 2

    completed_runs = db_session.scalars(select(PipelineRun).where(*_replay_score_date_filters())).all()
    assert len(completed_runs) == 1
    assert completed_runs[0].inputs == {"start_date": REPLAY_START, "end_date": REPLAY_END}


def test_replay_week_cli_records_run(cli_runner, db_session) -> None:
    result = cli_runner.invoke(app, ["replay-week", REPLAY_START, REPLAY_END])
    assert result.exit_code == 0
    assert "replayed 2026-03-30 to 2026-04-06" in result.stdout

    row = db_session.scalar(select(PipelineRun).where(*_replay_filters()))
    assert row is not None
    assert row.status == "completed"


def test_replay_week_rolls_back_on_failure(db_session, monkeypatch) -> None:
    def fail(*, session, score_date):
        raise RuntimeError("boom")

    monkeypatch.setattr("ai_thesis_monitor.ops.replay.service.run_weekly_pipeline", fail)

    with pytest.raises(RuntimeError):
        replay_week(db_session, start_date=REPLAY_START, end_date=REPLAY_END)

    db_session.expire_all()
    assert db_session.scalar(select(func.count()).select_from(PipelineRun)) == 0


def test_replay_week_failure_does_not_block_retry_until_caller_rollback(db_session, monkeypatch) -> None:
    second_lock_attempted = Event()
    second_outcome: Queue[ReplayResult | BaseException] = Queue(maxsize=1)
    bind = db_session.get_bind()
    lock_attempts = {"count": 0}
    pipeline_attempts = {"count": 0}
    transaction = db_session.begin()
    sentinel = Source(
        source_key="replay_failure_guard",
        source_name="Replay Failure Guard",
        source_type="test",
        base_url="https://example.test/failure",
        config={"guard": "failure"},
        reliability_score=0.61,
        active=True,
    )
    db_session.add(sentinel)
    db_session.flush()
    sentinel_id = sentinel.id

    def record_lock_attempt(session, lock_id):
        lock_attempts["count"] += 1
        if lock_attempts["count"] == 2:
            second_lock_attempted.set()
        return acquire_replay_lock(session, lock_id)

    def fail_once(*, session, score_date):
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
            session.close()

    thread = Thread(target=run_second_replay)
    thread.start()

    try:
        assert second_lock_attempted.wait(timeout=2)
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

        assert outcome.module_scores_written == 2
        assert len(completed_runs) == 1
    finally:
        transaction.rollback()
        thread.join(timeout=2)


def test_replay_week_fast_path_releases_lock(db_session) -> None:
    replay_week(db_session, start_date=REPLAY_START, end_date=REPLAY_END)
    second = replay_week(db_session, start_date=REPLAY_START, end_date=REPLAY_END)
    assert second.module_scores_written == 0
    assert not db_session.in_nested_transaction()


def test_replay_week_second_session_fast_paths_without_waiting_for_caller_transaction(
    db_session, monkeypatch
) -> None:
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
            session.close()

    thread = Thread(target=run_second_replay)
    thread.start()

    try:
        assert second_lock_attempted.wait(timeout=2)
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


def _seed_weekly_inputs(db_session, *, score_date: date) -> None:
    source = Source(
        source_key="replay_weekly_source",
        source_name="Replay Weekly Source",
        source_type="test",
        base_url="https://example.test/replay-weekly",
        config={},
        reliability_score=0.79,
        active=True,
    )
    metric_definition = MetricDefinition(
        metric_key="software_postings_yoy",
        module_key="labor",
        name="Software Job Postings YoY",
        description="Synthetic test metric for replay scoring",
        frequency="weekly",
        unit="index",
        lag_category="short",
        weight=1.2,
        expected_direction_citadel="up",
        expected_direction_citrini="down",
        primary_feature_key="value",
        signal_transform="identity",
        min_history_points=1,
        is_leading=True,
        config={},
        is_active=True,
    )
    db_session.add(source)
    db_session.add(metric_definition)
    db_session.flush()

    raw_observation = RawObservation(
        source_id=source.id,
        external_id="replay-weekly-raw",
        payload={"kind": "replay-weekly"},
        content_hash="replay-weekly-raw",
        published_at=datetime(2026, 4, 5, tzinfo=timezone.utc),
    )
    db_session.add(raw_observation)
    db_session.flush()

    document = Document(
        source_id=source.id,
        raw_observation_id=raw_observation.id,
        title="Replay weekly labor evidence",
        url="https://example.test/replay/weekly/labor",
        body_text="Synthetic replay weekly evidence body",
        published_at=raw_observation.published_at,
    )
    db_session.add(document)
    db_session.flush()

    chunk = DocumentChunk(
        document_id=document.id,
        chunk_index=0,
        chunk_text="Synthetic replay weekly evidence chunk",
        chunk_hash="replay-weekly-chunk",
    )
    db_session.add(chunk)
    db_session.flush()

    db_session.add(
        NormalizedMetric(
            metric_definition_id=metric_definition.id,
            source_id=source.id,
            raw_observation_id=raw_observation.id,
            geo=None,
            segment=None,
            observed_date=score_date,
            value=Decimal("-0.900"),
            quality_score=Decimal("0.850"),
            notes="Negative normalized trend for replay labor",
        )
    )
    db_session.add(
        Claim(
            source_id=source.id,
            raw_observation_id=raw_observation.id,
            document_id=document.id,
            chunk_id=chunk.id,
            module_key="labor",
            claim_type="headcount_reduction_ai_efficiency",
            entity="Replay Example Co",
            claim_text="Replay Example Co said AI efficiency reduced labor demand.",
            evidence_direction="citrini",
            strength=Decimal("0.900"),
            confidence=Decimal("0.850"),
            evidence_date=score_date,
            published_date=score_date,
            dedupe_key="replay-weekly-claim",
            review_status="pending_review",
        )
    )
    db_session.commit()
