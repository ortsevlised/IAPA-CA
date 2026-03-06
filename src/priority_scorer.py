from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class PriorityResult:
    score: int
    level: str
    rule_id: str
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def score_priority(
    extracted_fields: Mapping[str, Any],
    context: Mapping[str, Any] | None = None,
) -> PriorityResult:
    """
    DMN-equivalent first-hit rule scoring.

    Inputs used (DMN-aligned):
    - orderTotal
    - orderType
    - isExpedited
    - isMonthEnd
    """
    context = context or {}

    order_total = _to_float(extracted_fields.get("order_total")) or 0.0
    _order_type = str(extracted_fields.get("order_type") or "").strip().lower()
    is_expedited = bool(context.get("is_expedited", False))
    is_month_end = bool(context.get("is_month_end", False))

    # FIRST-hit policy (top-down) - exact mapping from provided DMN table.
    if is_expedited:
        return PriorityResult(
            score=100,
            level="CRITICAL",
            rule_id="Rule_1",
            rationale="Any expedited order overrides to CRITICAL",
        )
    if order_total >= 10000 and is_month_end:
        return PriorityResult(
            score=95,
            level="CRITICAL",
            rule_id="Rule_2",
            rationale="High-value order during month/quarter end",
        )
    if order_total >= 10000:
        return PriorityResult(
            score=85,
            level="HIGH",
            rule_id="Rule_3",
            rationale="High-value order during normal period",
        )
    if 5000 <= order_total <= 9999 and is_month_end:
        return PriorityResult(
            score=80,
            level="HIGH",
            rule_id="Rule_4",
            rationale="Mid-high value during month/quarter end",
        )
    if 5000 <= order_total <= 9999:
        return PriorityResult(
            score=65,
            level="MEDIUM",
            rule_id="Rule_5",
            rationale="Mid-high value during normal period",
        )
    if 500 <= order_total <= 4999 and is_month_end:
        return PriorityResult(
            score=60,
            level="MEDIUM",
            rule_id="Rule_6",
            rationale="Mid value during month/quarter end",
        )
    if 500 <= order_total <= 4999:
        return PriorityResult(
            score=45,
            level="MEDIUM",
            rule_id="Rule_7",
            rationale="Mid value during normal period",
        )
    if order_total < 500 and is_month_end:
        return PriorityResult(
            score=40,
            level="LOW",
            rule_id="Rule_8",
            rationale="Low value during month/quarter end",
        )
    return PriorityResult(
        score=20,
        level="LOW",
        rule_id="Rule_9",
        rationale="Low value during normal period (default)",
    )


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
