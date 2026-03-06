from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class DuplicateCheckResult:
    is_duplicate: bool
    match_type: str
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def check_duplicate_po(
    payload: Mapping[str, Any],
    existing_records: Sequence[Mapping[str, Any]],
) -> DuplicateCheckResult:
    """
    Deterministic duplicate check using PO number and customer ID.

    Matching policy:
    - Strong match: po_number + customer_id.
    - Weak match: po_number only (customer missing on one side).

    Data source:
    - `existing_records` is treated as the response payload from Salesforce SOQL.
    - In this PoC, Salesforce is mocked; no live API call is performed.
    """
    po_number = _norm(payload.get("po_number"))
    customer_id = _norm(payload.get("customer_id"))

    if not po_number:
        return DuplicateCheckResult(
            is_duplicate=False,
            match_type="none",
            rationale="Cannot run duplicate check without po_number",
        )

    for record in existing_records:
        existing_po = _norm(record.get("po_number"))
        if existing_po != po_number:
            continue

        existing_customer = _norm(record.get("customer_id"))
        if customer_id and existing_customer and customer_id == existing_customer:
            return DuplicateCheckResult(
                is_duplicate=True,
                match_type="po_number+customer_id",
                rationale="Duplicate detected on po_number and customer_id",
            )

        return DuplicateCheckResult(
            is_duplicate=True,
            match_type="po_number",
            rationale="Potential duplicate detected on po_number",
        )

    return DuplicateCheckResult(
        is_duplicate=False,
        match_type="none",
        rationale="No duplicate found in existing records",
    )


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def get_existing_records_from_salesforce_mock(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    """
    Mocked Salesforce duplicate lookup.

    This keeps Phase 1 fully local while preserving the contract we'd use for a real SOQL query.
    Expected shape of each record: {"po_number": "...", "customer_id": "..."}.
    """
    records = payload.get("existing_records", [])
    return [dict(r) for r in records if isinstance(r, Mapping)]
