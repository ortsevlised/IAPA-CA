from __future__ import annotations

from typing import Any, Mapping

from .ai_extractor import extract_with_ai_ocr_stub
from .classifier import classify_po_format_and_source
from .duplicate_checker import check_duplicate_po, get_existing_records_from_salesforce_mock
from .output_formatter import emit_downstream_json
from .priority_scorer import score_priority
from .template_extractor import extract_with_template, should_use_template_path
from .validator import DEFAULT_AI_CONFIDENCE_THRESHOLD, validate_extraction


def run_classification_step(payload: Mapping[str, Any]) -> dict[str, Any]:
    result = classify_po_format_and_source(payload)
    return {
        "stage": "classify_po_format_source",
        "classification": result.to_dict(),
        "input": {
            "filename": payload.get("filename"),
            "mime_type": payload.get("mime_type"),
            "source": payload.get("source"),
            "channel": payload.get("channel"),
        },
    }


def run_classification_and_duplicate_step(payload: Mapping[str, Any]) -> dict[str, Any]:
    classification_output = run_classification_step(payload)
    existing_records = get_existing_records_from_salesforce_mock(payload)
    duplicate_result = check_duplicate_po(
        payload=payload,
        existing_records=existing_records,
    )

    return {
        "stage": "classify_and_check_duplicates",
        "classification": classification_output["classification"],
        "duplicate_check": duplicate_result.to_dict(),
        "halted": duplicate_result.is_duplicate,
        "halt_reason": "duplicate_po" if duplicate_result.is_duplicate else None,
        "input": classification_output["input"],
        "keys": {
            "po_number": payload.get("po_number"),
            "customer_id": payload.get("customer_id"),
        },
    }


def run_phase1_step3(payload: Mapping[str, Any]) -> dict[str, Any]:
    step2_output = run_classification_and_duplicate_step(payload)
    if step2_output["halted"]:
        return {
            **step2_output,
            "stage": "classify_duplicate_extract",
            "extraction": None,
        }

    if should_use_template_path(payload):
        extraction = extract_with_template(payload).to_dict()
    else:
        extraction = extract_with_ai_ocr_stub(payload).to_dict()

    return {
        **step2_output,
        "stage": "classify_duplicate_extract",
        "extraction": extraction,
    }


def run_phase1_step4(payload: Mapping[str, Any]) -> dict[str, Any]:
    step3_output = run_phase1_step3(payload)

    if step3_output["halted"]:
        return {
            **step3_output,
            "stage": "classify_duplicate_extract_validate",
            "validation": None,
            "manual_fallback": False,
        }

    threshold = float(payload.get("validation_threshold", DEFAULT_AI_CONFIDENCE_THRESHOLD))
    validation = validate_extraction(step3_output["extraction"], threshold=threshold).to_dict()

    return {
        **step3_output,
        "stage": "classify_duplicate_extract_validate",
        "validation": validation,
        "manual_fallback": validation["requires_manual_fallback"],
    }


def run_phase1_step5(payload: Mapping[str, Any]) -> dict[str, Any]:
    step4_output = run_phase1_step4(payload)

    if step4_output["halted"]:
        return {
            **step4_output,
            "stage": "classify_duplicate_extract_validate_score",
            "priority": None,
            "priority_skipped_reason": "duplicate_po",
        }

    if step4_output["manual_fallback"]:
        return {
            **step4_output,
            "stage": "classify_duplicate_extract_validate_score",
            "priority": None,
            "priority_skipped_reason": "manual_fallback_required",
        }

    extracted_fields = step4_output["extraction"]["extracted_fields"]
    context = {
        "is_expedited": payload.get("is_expedited", payload.get("isExpedited", False)),
        "is_month_end": payload.get("is_month_end", payload.get("isMonthEnd", payload.get("is_period_end", False))),
    }
    priority = score_priority(extracted_fields, context=context).to_dict()

    return {
        **step4_output,
        "stage": "classify_duplicate_extract_validate_score",
        "priority": priority,
        "priority_skipped_reason": None,
    }


def run_phase1_step6(payload: Mapping[str, Any]) -> dict[str, Any]:
    step5_output = run_phase1_step5(payload)
    return emit_downstream_json(step5_output=step5_output, payload=payload)
