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


def test_build_weekly_summary_identifies_strongest_module_by_regime() -> None:
    summary = build_weekly_summary(
        overall_winner="citrini",
        module_regimes={
            "labor": "neutral",
            "productivity": "strong_citrini",
            "services": "leaning_citrini",
        },
        new_evidence=[],
        open_questions=[],
    )
    assert "productivity" in summary
    assert "strong_citrini" in summary


def test_build_weekly_summary_favors_winner_aligned_regime_priority() -> None:
    summary = build_weekly_summary(
        overall_winner="citadel",
        module_regimes={
            "labor": "strong_citadel",
            "services": "leaning_citrini",
        },
        new_evidence=[],
        open_questions=[],
    )
    assert "labor" in summary
    assert "strong_citadel" in summary
