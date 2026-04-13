from ai_thesis_monitor.ingestion.pipelines.weekly import run_weekly_pipeline


def test_run_weekly_pipeline_handles_modules_without_history() -> None:
    result = run_weekly_pipeline(
        module_histories={"labor": []},
        critical_claims={"labor": ["claim"]},
    )

    assert result.module_scores_written == 0
    assert result.tripwires_written == 0
    assert result.alerts_written == 0
    assert result.narratives_written == 1
