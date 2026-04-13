from ai_thesis_monitor.domain.narratives.build import build_weekly_summary


def test_build_weekly_summary_mentions_leading_thesis_and_open_questions() -> None:
    summary = build_weekly_summary(
        overall_winner="citrini",
        module_regimes={"labor": "strong_citrini", "productivity": "neutral"},
        new_evidence=["software postings worsened", "ServiceNow AI layoff claim pending review"],
        open_questions=["demand spillover remains unconfirmed"],
    )
    assert "citrini" in summary.lower()
    assert "unconfirmed" in summary.lower()
