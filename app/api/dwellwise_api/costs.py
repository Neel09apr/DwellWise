"""A development cost estimate: every figure is the user's own input, and each line shows its working.

Deterministic arithmetic, no database and no model. It estimates what building
a scheme might cost; it never values a site and never says what will be built.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .schemas import CostLine, Costs

NOTE = (
    "Excludes VAT. Every rate is yours: check your council's current development contribution "
    "scheme, including any waiver, before relying on that line. An estimate, not a valuation."
)


@dataclass(frozen=True)
class Inputs:
    homes: int
    floor_area_m2: float  # per home
    build_cost_per_m2: float
    contribution: float  # euro, per m2 or per home
    contribution_basis: Literal["per_m2", "per_home"]
    fees_pct: float  # of build cost
    contingency_pct: float  # of build cost
    finance_rate_pct: float  # a year
    finance_months: int
    land: float = 0.0


def _eur(value: float) -> str:
    return f"€{value:,.0f}"


def _n(value: float) -> str:
    return f"{value:,g}"


def estimate(i: Inputs) -> Costs:
    """Land, build, contributions, fees, contingency and finance, each with the arithmetic used."""
    area = i.homes * i.floor_area_m2
    build = area * i.build_cost_per_m2
    if i.contribution_basis == "per_m2":
        contributions = area * i.contribution
        contribution_working = f"{_n(area)} m² × {_eur(i.contribution)} per m²"
    else:
        contributions = i.homes * i.contribution
        contribution_working = f"{i.homes} homes × {_eur(i.contribution)} per home"
    fees = build * i.fees_pct / 100
    contingency = build * i.contingency_pct / 100
    before_finance = i.land + build + contributions + fees + contingency
    # ponytail: an even drawdown, so on average half the cost is borrowed; a cash-flow model can replace it.
    finance = before_finance / 2 * i.finance_rate_pct / 100 * i.finance_months / 12

    lines = [CostLine(item="Land", amount=round(i.land), working="As entered")] if i.land else []
    lines += [
        CostLine(
            item="Build",
            amount=round(build),
            working=f"{i.homes} homes × {_n(i.floor_area_m2)} m² × {_eur(i.build_cost_per_m2)} per m²",
        ),
        CostLine(item="Development contributions", amount=round(contributions), working=contribution_working),
        CostLine(item="Professional fees", amount=round(fees), working=f"{_n(i.fees_pct)}% of build"),
        CostLine(item="Contingency", amount=round(contingency), working=f"{_n(i.contingency_pct)}% of build"),
        CostLine(
            item="Finance",
            amount=round(finance),
            working=(
                f"{_n(i.finance_rate_pct)}% a year for {i.finance_months} months "
                f"on half of {_eur(before_finance)}, as if drawn evenly"
            ),
        ),
    ]
    total = sum(line.amount for line in lines)
    return Costs(
        homes=i.homes,
        floor_area_m2=area,
        lines=lines,
        total=total,
        per_home=round(total / i.homes),
        note=NOTE,
    )
