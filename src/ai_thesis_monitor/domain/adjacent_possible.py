"""Adjacent-possible query generator with Bradford-respecting distribution.

Motivation
----------
On 2026-05-10, an iterative web-search synthesis pass revealed a "third thesis"
(power/compute as agentic-deployment rate-limiter) that neither citrini nor
citadel had modeled. That synthesis only worked because of a corrective step
forcing 25%+ of queries to challenge the current lean (Bradford-style quota
applied to search intent, not just to ingested sources).

This module mechanizes that corrective step. Given the current scoring snapshot
("which thesis is leaning" + "by what margin"), it generates a structured query
plan with:

- ~40-50% queries confirming the current lean (cheap to find evidence; useful
  for tripwire detection)
- ~25-35% queries challenging the current lean (forces falsification attempts;
  matches metaxon Bradford 25% min for challenging)
- ~20-30% adjacent-possible queries (neither side's existing terms; third-thesis
  discovery territory)

Output is the QUERY PLAN, not search results. The plan is consumed by an
external search runner (e.g. Claude+WebSearch, or operator running them
manually). Keeping the plan separate from execution preserves auditability:
which queries were generated, with what intent, on what date.

Anti-pattern: do NOT auto-execute these queries via paid APIs without a cost
cap. Use the dry-run flag for plan-only output, or pipe to web-fetch tooling
with explicit budget.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Literal


class QueryIntent(str, Enum):
    """Why this query exists relative to current scoring."""

    CONFIRM_LEAN = "confirm_lean"
    CHALLENGE_LEAN = "challenge_lean"
    ADJACENT_POSSIBLE = "adjacent_possible"


@dataclass(frozen=True)
class QueryPlanItem:
    """One query in the structured plan."""

    query: str
    intent: QueryIntent
    rationale: str
    expected_thesis_signal: Literal["citadel", "citrini", "third", "ambiguous"]


@dataclass(frozen=True)
class QueryPlan:
    """Full plan emitted for a given scoring snapshot.

    Caller passes plan to a search runner. The plan itself is the audit
    artifact — confirms Bradford distribution at the moment of synthesis.
    """

    generated_on: date
    current_lean: Literal[
        "strong_citadel",
        "leaning_citadel",
        "neutral",
        "leaning_citrini",
        "strong_citrini",
    ]
    items: list[QueryPlanItem]
    bradford_ratios: dict[QueryIntent, float] = field(default_factory=dict)


# =============================================================================
# Query templates — neutral phrasing avoids loaded terms.
# Update these as the empirical landscape shifts.
# =============================================================================

_CITADEL_CONFIRMING_QUERIES = [
    "AI productivity gains GDP {year} employment net positive Goldman Sachs JPMorgan",
    "SaaS revenue resilience {year} enterprise spending growth CRM observability moats",
    "AI augmentation experienced workers productivity gains {year}",
    "tech hiring stable {year} senior engineers software demand",
    "Engels Pause modern AI labor adjustment economic history",
]

_CITRINI_CONFIRMING_QUERIES = [
    "TCS Infosys Wipro {year} hiring layoffs revenue guidance AI impact",
    "Brynjolfsson AI labor displacement young workers {year}",
    "software engineer hiring decline AI {year} white collar unemployment",
    "PE backed SaaS distress defaults {year} agentic coding",
    "SaaS pricing collapse agentic coding tools enterprise procurement {year}",
]

_ADJACENT_POSSIBLE_QUERIES = [
    "AI compute energy bottleneck {year} capacity constraints chip shortage data center",
    "labor force participation prime age {year} hours worked total nonfarm payrolls",
    "transformer lead time grid interconnect data center {year}",
    "open-source LLM enterprise self-hosting deflation cost curve {year}",
    "geopolitical AI chip export controls reshoring effects {year}",
    "agentic AI failure modes enterprise production reliability {year}",
    "AI insurance liability regulatory risk enterprise adoption {year}",
]


# =============================================================================
# Bradford ratios per current lean.
# Reasoning: if currently leaning citrini, ask MORE citadel-confirming questions
# to test the lean. If neutral, balance across both.
# =============================================================================

_BRADFORD_RATIOS: dict[str, dict[QueryIntent, float]] = {
    "strong_citrini": {
        QueryIntent.CONFIRM_LEAN: 0.30,  # cheap citrini-confirming
        QueryIntent.CHALLENGE_LEAN: 0.45,  # heavy citadel-leaning to test lean
        QueryIntent.ADJACENT_POSSIBLE: 0.25,
    },
    "leaning_citrini": {
        QueryIntent.CONFIRM_LEAN: 0.35,
        QueryIntent.CHALLENGE_LEAN: 0.40,
        QueryIntent.ADJACENT_POSSIBLE: 0.25,
    },
    "neutral": {
        QueryIntent.CONFIRM_LEAN: 0.40,
        QueryIntent.CHALLENGE_LEAN: 0.30,  # symmetric since no lean
        QueryIntent.ADJACENT_POSSIBLE: 0.30,
    },
    "leaning_citadel": {
        QueryIntent.CONFIRM_LEAN: 0.35,
        QueryIntent.CHALLENGE_LEAN: 0.40,
        QueryIntent.ADJACENT_POSSIBLE: 0.25,
    },
    "strong_citadel": {
        QueryIntent.CONFIRM_LEAN: 0.30,
        QueryIntent.CHALLENGE_LEAN: 0.45,
        QueryIntent.ADJACENT_POSSIBLE: 0.25,
    },
}


def build_query_plan(
    *,
    current_lean: str,
    n_queries: int = 12,
    year: int | None = None,
    today: date | None = None,
) -> QueryPlan:
    """Build a Bradford-respecting query plan for current scoring snapshot.

    Args:
        current_lean: One of the five regime strings (strong_citadel ... strong_citrini).
        n_queries: Total number of queries to generate. Default 12 (cheap to run via
            WebSearch). Bump to 20+ for thorough scout passes.
        year: Year to substitute in templated queries (default: today's year).
        today: Override for plan emission date (default: today).

    Returns:
        QueryPlan with items distributed per the lean-specific Bradford ratios.
        Caller is responsible for executing the queries; this fn only plans.
    """
    today = today or date.today()
    year = year or today.year
    if current_lean not in _BRADFORD_RATIOS:
        raise ValueError(
            f"unknown lean {current_lean!r}; expected one of {list(_BRADFORD_RATIOS)}"
        )

    ratios = _BRADFORD_RATIOS[current_lean]
    n_by_intent = _allocate(n_queries, ratios)

    if current_lean.endswith("citrini"):
        confirming_pool = _CITRINI_CONFIRMING_QUERIES
        challenging_pool = _CITADEL_CONFIRMING_QUERIES
        confirming_signal = "citrini"
        challenging_signal = "citadel"
    elif current_lean.endswith("citadel"):
        confirming_pool = _CITADEL_CONFIRMING_QUERIES
        challenging_pool = _CITRINI_CONFIRMING_QUERIES
        confirming_signal = "citadel"
        challenging_signal = "citrini"
    else:  # neutral
        confirming_pool = _CITADEL_CONFIRMING_QUERIES + _CITRINI_CONFIRMING_QUERIES
        challenging_pool = _CITRINI_CONFIRMING_QUERIES + _CITADEL_CONFIRMING_QUERIES
        confirming_signal = "ambiguous"
        challenging_signal = "ambiguous"

    items: list[QueryPlanItem] = []
    items.extend(
        _items_from_pool(
            pool=confirming_pool,
            intent=QueryIntent.CONFIRM_LEAN,
            year=year,
            n=n_by_intent[QueryIntent.CONFIRM_LEAN],
            expected_signal=confirming_signal,
            rationale=f"Confirm current {current_lean} lean by sampling supporting evidence.",
        )
    )
    items.extend(
        _items_from_pool(
            pool=challenging_pool,
            intent=QueryIntent.CHALLENGE_LEAN,
            year=year,
            n=n_by_intent[QueryIntent.CHALLENGE_LEAN],
            expected_signal=challenging_signal,
            rationale=(
                f"Bradford-mandated falsification probe — search for evidence that "
                f"contradicts current {current_lean} reading."
            ),
        )
    )
    items.extend(
        _items_from_pool(
            pool=_ADJACENT_POSSIBLE_QUERIES,
            intent=QueryIntent.ADJACENT_POSSIBLE,
            year=year,
            n=n_by_intent[QueryIntent.ADJACENT_POSSIBLE],
            expected_signal="third",
            rationale=(
                "Adjacent-possible probe — neither thesis's terms. Aims at "
                "third-thesis discovery (e.g. power bottleneck, regulatory regime "
                "shift, geopolitical decoupling). Where surprises live."
            ),
        )
    )

    return QueryPlan(
        generated_on=today,
        current_lean=current_lean,  # type: ignore[arg-type]
        items=items,
        bradford_ratios=ratios,
    )


def _allocate(total: int, ratios: dict[QueryIntent, float]) -> dict[QueryIntent, int]:
    """Allocate total queries across intents per ratios, preserving sum."""
    raw = {intent: total * r for intent, r in ratios.items()}
    rounded = {intent: int(round(v)) for intent, v in raw.items()}
    diff = total - sum(rounded.values())
    if diff != 0:
        # Push the diff onto the largest-share intent.
        target = max(rounded, key=lambda k: ratios[k])
        rounded[target] += diff
    return rounded


def _items_from_pool(
    *,
    pool: list[str],
    intent: QueryIntent,
    year: int,
    n: int,
    expected_signal: str,
    rationale: str,
) -> list[QueryPlanItem]:
    """Sample n queries from pool with year interpolation."""
    if n <= 0 or not pool:
        return []
    # Deterministic: take the first n (no shuffle) so plans are reproducible
    # for a given (lean, n, year) tuple. Caller can shuffle in CLI if desired.
    selected = pool[:n] if n <= len(pool) else pool * (n // len(pool) + 1)
    return [
        QueryPlanItem(
            query=template.format(year=year),
            intent=intent,
            rationale=rationale,
            expected_thesis_signal=expected_signal,  # type: ignore[arg-type]
        )
        for template in selected[:n]
    ]


def render_plan_markdown(plan: QueryPlan) -> str:
    """Render a QueryPlan as human-readable markdown.

    Use case: paste to operator running queries manually, or wrap as input
    to a Claude+WebSearch session.
    """
    lines = [
        f"# Adjacent-possible query plan — {plan.generated_on.isoformat()}",
        "",
        f"**Current lean:** `{plan.current_lean}`  ",
        f"**Total queries:** {len(plan.items)}  ",
        "",
        "## Bradford distribution",
        "",
        "| Intent | Target ratio | Count |",
        "| --- | --- | --- |",
    ]
    counts_by_intent: dict[QueryIntent, int] = {}
    for item in plan.items:
        counts_by_intent[item.intent] = counts_by_intent.get(item.intent, 0) + 1
    for intent, ratio in plan.bradford_ratios.items():
        n = counts_by_intent.get(intent, 0)
        lines.append(f"| `{intent.value}` | {ratio:.2f} | {n} |")

    lines.extend(["", "## Queries", ""])
    for i, item in enumerate(plan.items, start=1):
        lines.extend(
            [
                f"### Q{i}. [{item.intent.value} — signal: {item.expected_thesis_signal}]",
                "",
                f"> {item.query}",
                "",
                f"_{item.rationale}_",
                "",
            ]
        )

    return "\n".join(lines)
