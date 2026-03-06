from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


DEFAULT_AI_CONFIDENCE_THRESHOLD = 0.70


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    requires_manual_fallback: bool
    threshold: float | None
    confidence: float | None
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_extraction(extraction: Mapping[str, Any], threshold: float = DEFAULT_AI_CONFIDENCE_THRESHOLD) -> ValidationResult:
    """
    Validate extraction output quality.

    Policy:
    - Template path: deterministic, accepted in this PoC.
    - AI/OCR path: must meet confidence threshold or route to manual fallback.
    """
    path = str(extraction.get("extraction_path", "")).strip().lower()

    if path == "template":
        return ValidationResult(
            is_valid=True,
            requires_manual_fallback=False,
            threshold=None,
            confidence=None,
            rationale="Template extraction accepted (deterministic path)",
        )

    if path == "ai_ocr_stub":
        confidence = _to_float(extraction.get("confidence"))
        if confidence is None:
            return ValidationResult(
                is_valid=False,
                requires_manual_fallback=True,
                threshold=threshold,
                confidence=None,
                rationale="AI/OCR extraction missing confidence; routed to manual fallback",
            )

        if confidence >= threshold:
            return ValidationResult(
                is_valid=True,
                requires_manual_fallback=False,
                threshold=threshold,
                confidence=confidence,
                rationale="AI/OCR extraction confidence meets threshold",
            )

        return ValidationResult(
            is_valid=False,
            requires_manual_fallback=True,
            threshold=threshold,
            confidence=confidence,
            rationale="AI/OCR extraction confidence below threshold; routed to manual fallback",
        )

    return ValidationResult(
        is_valid=False,
        requires_manual_fallback=True,
        threshold=threshold,
        confidence=None,
        rationale="Unknown extraction path; routed to manual fallback",
    )


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
