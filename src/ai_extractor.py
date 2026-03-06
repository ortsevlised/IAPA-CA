from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from .template_extractor import _extract_fields


@dataclass(frozen=True)
class AIExtractionResult:
    extraction_path: str
    model: str
    confidence: float
    extracted_fields: dict[str, Any]
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def extract_with_ai_ocr_stub(payload: Mapping[str, Any]) -> AIExtractionResult:
    """
    AI/OCR extraction stub for unstructured layouts.

    In this PoC we do not call a live model. We simulate model output and confidence.
    """
    model = str(payload.get("ai_model", "qwen-vl-stub"))
    confidence = _bounded_confidence(payload.get("ai_stub_confidence", 0.72))

    extracted_fields = dict(payload.get("ai_stub_result") or _extract_fields(payload))

    return AIExtractionResult(
        extraction_path="ai_ocr_stub",
        model=model,
        confidence=confidence,
        extracted_fields=extracted_fields,
        rationale=f"Used AI/OCR fallback stub model: {model}",
    )


def _bounded_confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        confidence = 0.0
    return max(0.0, min(1.0, round(confidence, 2)))
