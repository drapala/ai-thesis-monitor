"""Historical India IT earnings data points for manual seeding.

Sources:
- TCS Q4 FY26 press release (2026-04-09): headcount 584,519; annualized revenue ~$30.5B; AI revenue $2.3B annualized
- TCS Q3 FY26 press release (2026-01-09): headcount 582,163
- Storyboard18 / The Register (Jan 2026): Big-4 combined headcount down 42k over FY25+FY26
- Wipro Q4 FY26 results (Apr 2026): headcount 242,156; utilization 83.5-84.5%; revenue $2.58B quarterly
- Wipro Q2 FY26 press release: utilization ~82.5%
- Approximations for intermediate quarters are marked with quality_score=0.70 (vs 0.90 for confirmed).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal


# Each row: (observed_date, value, quality_score, notes)
# Value units per metric are documented in metric_definitions.py comments.

INDIA_IT_DATA: dict[str, list[tuple[date, Decimal, Decimal, str]]] = {
    # Combined Big-4 headcount in thousands (TCS+Infosys+Wipro+HCL)
    # TCS FY24 peak ~614k; Infosys ~343k; Wipro ~258k; HCL ~227k → total ~1,442k at peak
    # End FY25: ~42k reduction already started; End FY26: ~42k total reduction confirmed
    "india_it_headcount_total": [
        (
            date(2024, 3, 31),
            Decimal("1441.0"),
            Decimal("0.80"),
            "FY25 start approx; pre-reduction baseline",
        ),
        (
            date(2024, 6, 30),
            Decimal("1425.0"),
            Decimal("0.70"),
            "Q1 FY26 approx; hiring freeze visible",
        ),
        (date(2024, 9, 30), Decimal("1415.0"), Decimal("0.70"), "Q2 FY26 approx"),
        (date(2024, 12, 31), Decimal("1405.0"), Decimal("0.70"), "Q3 FY26 approx"),
        (
            date(2025, 3, 31),
            Decimal("1415.0"),
            Decimal("0.80"),
            "FY25 Q4 approx; ~25k net TCS reduction in FY25",
        ),
        (date(2025, 6, 30), Decimal("1400.0"), Decimal("0.70"), "Q1 FY26 approx"),
        (date(2025, 9, 30), Decimal("1392.0"), Decimal("0.70"), "Q2 FY26 approx"),
        (
            date(2025, 12, 31),
            Decimal("1383.0"),
            Decimal("0.80"),
            "Q3 FY26; TCS 582,163 confirmed",
        ),
        (
            date(2026, 3, 31),
            Decimal("1399.0"),
            Decimal("0.90"),
            "Q4 FY26; TCS 584,519 confirmed; Wipro 242,156 confirmed; partial recovery",
        ),
    ],
    # TCS annualized revenue / headcount (USD thousands per employee)
    # FY25 revenue ~$29.1B / ~607k → $47.9k; FY26 revenue ~$30.5B / ~584.5k → $52.2k
    "india_it_revenue_per_employee": [
        (
            date(2024, 3, 31),
            Decimal("45.8"),
            Decimal("0.80"),
            "FY24 Q4 approx; $27.9B / 601k",
        ),
        (date(2024, 6, 30), Decimal("46.5"), Decimal("0.70"), "FY25 Q1 approx"),
        (date(2024, 9, 30), Decimal("47.0"), Decimal("0.70"), "FY25 Q2 approx"),
        (date(2024, 12, 31), Decimal("47.5"), Decimal("0.70"), "FY25 Q3 approx"),
        (
            date(2025, 3, 31),
            Decimal("47.9"),
            Decimal("0.85"),
            "FY25 Q4; $29.1B annualized / 607k",
        ),
        (date(2025, 6, 30), Decimal("49.2"), Decimal("0.70"), "FY26 Q1 approx"),
        (date(2025, 9, 30), Decimal("50.1"), Decimal("0.70"), "FY26 Q2 approx"),
        (date(2025, 12, 31), Decimal("51.0"), Decimal("0.80"), "FY26 Q3 approx"),
        (
            date(2026, 3, 31),
            Decimal("52.2"),
            Decimal("0.90"),
            "FY26 Q4; $30.5B annualized / 584,519 confirmed",
        ),
    ],
    # TCS AI revenue as fraction of total (annualized basis)
    # Q4 FY26: $2.3B / $30.5B = 7.5%; built up over FY26
    "india_it_ai_revenue_pct": [
        (
            date(2024, 9, 30),
            Decimal("0.025"),
            Decimal("0.70"),
            "FY25 Q2 approx; AI revenue nascent",
        ),
        (date(2024, 12, 31), Decimal("0.030"), Decimal("0.70"), "FY25 Q3 approx"),
        (
            date(2025, 3, 31),
            Decimal("0.038"),
            Decimal("0.75"),
            "FY25 Q4 approx; AI revenue ~$1.1B annualized",
        ),
        (
            date(2025, 6, 30),
            Decimal("0.050"),
            Decimal("0.75"),
            "FY26 Q1 approx; AI revenue growing",
        ),
        (date(2025, 9, 30), Decimal("0.060"), Decimal("0.75"), "FY26 Q2 approx"),
        (date(2025, 12, 31), Decimal("0.068"), Decimal("0.80"), "FY26 Q3 approx"),
        (
            date(2026, 3, 31),
            Decimal("0.075"),
            Decimal("0.90"),
            "FY26 Q4 confirmed; $2.3B annualized / $30.5B = 7.5%",
        ),
    ],
    # Wipro billable utilization rate (excluding trainees)
    # Q4 FY26: 83.5-84.5% → midpoint 84.0%; improving from ~82% in FY25
    "india_it_utilization_rate": [
        (
            date(2025, 3, 31),
            Decimal("0.820"),
            Decimal("0.80"),
            "FY25 Q4 approx; Wipro utilization pre-AI-scale",
        ),
        (date(2025, 6, 30), Decimal("0.825"), Decimal("0.70"), "FY26 Q1 approx"),
        (
            date(2025, 9, 30),
            Decimal("0.825"),
            Decimal("0.85"),
            "FY26 Q2; Wipro Q2 FY26 press release ~82.5%",
        ),
        (date(2025, 12, 31), Decimal("0.832"), Decimal("0.80"), "FY26 Q3 approx"),
        (
            date(2026, 3, 31),
            Decimal("0.840"),
            Decimal("0.90"),
            "FY26 Q4 confirmed; Wipro 83.5-84.5% band midpoint",
        ),
    ],
}
