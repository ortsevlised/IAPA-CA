from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping


KNOWN_TEMPLATE_IDS = {"distributor_v1", "reseller_standard_v2"}


@dataclass(frozen=True)
class TemplateExtractionResult:
    extraction_path: str
    template_id: str
    extracted_fields: dict[str, Any]
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def should_use_template_path(payload: Mapping[str, Any]) -> bool:
    template_id = str(payload.get("template_id", "")).strip().lower()
    return template_id in KNOWN_TEMPLATE_IDS


def extract_with_template(payload: Mapping[str, Any]) -> TemplateExtractionResult:
    template_id = str(payload.get("template_id", "")).strip().lower()
    normalized_template_id = template_id if template_id in KNOWN_TEMPLATE_IDS else "unmapped_template"

    return TemplateExtractionResult(
        extraction_path="template",
        template_id=normalized_template_id,
        extracted_fields=_extract_fields(payload),
        rationale=f"Used deterministic template mapping: {normalized_template_id}",
    )


def _extract_fields(payload: Mapping[str, Any]) -> dict[str, Any]:
    text = str(payload.get("text", ""))

    po_number = payload.get("po_number") or _search(text, r"\bPO[-\s]?\d{2,}\b")
    customer_id = payload.get("customer_id") or _search(text, r"\bCUST[-\s]?\d{1,}\b")
    order_total = payload.get("order_total") or _search(text, r"\b(?:USD|\\$)\s?(\d+(?:\.\d{2})?)\b", group=1)
    order_type = payload.get("order_type") or _search(text, r"\b(new|renewal|upgrade|maintenance)\b")

    return {
        "po_number": po_number,
        "customer_id": customer_id,
        "order_total": _to_float(order_total),
        "order_type": str(order_type).lower() if order_type else None,
        "currency": payload.get("currency") or "USD",
    }


def _search(text: str, pattern: str, group: int = 0) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(group)


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
