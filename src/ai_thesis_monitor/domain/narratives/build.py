"""Narrative summarization helpers."""

from __future__ import annotations


def build_weekly_summary(
    *,
    overall_winner: str,
    module_regimes: dict[str, str],
    new_evidence: list[str],
    open_questions: list[str],
) -> str:
    regime_priority = {
        "strong_citrini": 0,
        "leaning_citrini": 1,
        "neutral": 2,
        "leaning_citadel": 3,
        "strong_citadel": 4,
    }
    default_rank = max(regime_priority.values()) + 1
    strongest_module = min(
        module_regimes.items(),
        key=lambda item: regime_priority.get(item[1], default_rank),
        default=("system", "neutral"),
    )
    evidence_line = "; ".join(new_evidence[:2]) or "no new high-signal evidence"
    open_question_line = "; ".join(open_questions[:2]) or "no open questions"
    return (
        f"{overall_winner} leads this week. "
        f"Strongest visible module is {strongest_module[0]} with regime {strongest_module[1]}. "
        f"New evidence: {evidence_line}. "
        f"Still unconfirmed: {open_question_line}."
    )
