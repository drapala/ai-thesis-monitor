from ai_thesis_monitor.ops.replay.service import replay_week


def test_replay_week_is_idempotent(db_session) -> None:
    first = replay_week(db_session, start_date="2026-03-30", end_date="2026-04-06")
    second = replay_week(db_session, start_date="2026-03-30", end_date="2026-04-06")

    assert first.module_scores_written >= 0
    assert second.module_scores_written == 0
