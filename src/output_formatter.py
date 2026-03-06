from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping


SCHEMA_VERSION = "1.0.0"


def emit_downstream_json(
    step5_output: Mapping[str, Any],
    payload: Mapping[str, Any],
    generated_at: str | None = None,
) -> dict[str, Any]:
    timestamp = generated_at or _utc_now_iso()

    triage_id = str(payload.get("triage_id") or payload.get("po_number") or "unknown")
    region = _resolve_region(payload, step5_output)

    if step5_output.get("halted"):
        disposition = "REJECT_DUPLICATE"
        route = "stop"
        reason = step5_output.get("halt_reason")
    elif step5_output.get("manual_fallback"):
        disposition = "MANUAL_REVIEW"
        route = f"manual_queue_{region}"
        reason = "low_extraction_confidence"
    else:
        disposition = "READY_FOR_ORDER_FULFILLMENT"
        route = region
        reason = None

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": timestamp,
        "triage_id": triage_id,
        "region": region,
        "disposition": disposition,
        "route": route,
        "reason": reason,
        "priority": step5_output.get("priority"),
        "payload": dict(step5_output),
    }


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _resolve_region(payload: Mapping[str, Any], step5_output: Mapping[str, Any]) -> str:
    candidates = [
        payload.get("region"),
        payload.get("customer_region"),
        payload.get("country"),
        payload.get("country_code"),
        _dig(step5_output, "extraction", "extracted_fields", "region"),
        _dig(step5_output, "extraction", "extracted_fields", "country"),
    ]

    for value in candidates:
        mapped = _map_region(value)
        if mapped:
            return mapped
    return "USA"


def _map_region(value: Any) -> str | None:
    if value is None:
        return None

    raw = str(value).strip().upper()
    if not raw:
        return None

    if raw in {"USA", "US", "UNITED STATES"}:
        return "USA"
    if raw in {"EMEA", "EU", "UK", "GB", "FR", "DE", "IT", "ES", "NL", "UAE"}:
        return "EMEA"
    if raw in {"APAC", "IN", "CN", "JP", "AU", "NZ", "SG"}:
        return "APAC"
    return None


def _dig(data: Mapping[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current
