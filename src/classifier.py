from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

FORMAT_UNKNOWN = "unknown"
SOURCE_UNKNOWN = "unknown"


@dataclass(frozen=True)
class ClassificationResult:
    po_format: str
    source: str
    rationale: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def classify_po_format_and_source(payload: Mapping[str, Any]) -> ClassificationResult:
    """Classify inbound PO format and source using deterministic heuristics."""
    rationale: list[str] = []

    po_format, format_reason = _detect_format(payload)
    if format_reason:
        rationale.append(format_reason)

    source, source_reason = _detect_source(payload, po_format)
    if source_reason:
        rationale.append(source_reason)

    return ClassificationResult(
        po_format=po_format,
        source=source,
        rationale=rationale,
    )


def _detect_format(payload: Mapping[str, Any]) -> tuple[str, str]:
    mime = str(payload.get("mime_type", "")).lower()
    filename = str(payload.get("filename", "")).lower()
    text = str(payload.get("text", "")).strip()

    if mime == "application/pdf" or filename.endswith(".pdf"):
        return "pdf", "Detected PDF via MIME type or file extension"
    if mime in {"message/rfc822", "text/email"} or filename.endswith(".eml"):
        return "email", "Detected email payload via MIME type or .eml extension"
    if mime.startswith("text/") or filename.endswith(".txt"):
        return "text", "Detected plain text payload"
    if mime.startswith("image/") or filename.endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff")):
        return "image", "Detected image payload likely requiring OCR"
    if text:
        return "text", "No file metadata found; inferred text from inline content"
    return FORMAT_UNKNOWN, "Insufficient signals to determine PO format"


def _detect_source(payload: Mapping[str, Any], po_format: str) -> tuple[str, str]:
    source_hint = str(payload.get("source", "")).lower()
    channel_hint = str(payload.get("channel", "")).lower()
    sender = str(payload.get("sender", "")).lower()

    combined = " ".join([source_hint, channel_hint])

    if any(token in combined for token in ("email", "mailbox", "outlook")):
        source = "email_attachment" if po_format in {"pdf", "image", "text"} else "email"
        return source, "Detected email ingestion channel"

    if any(token in combined for token in ("portal", "web", "upload", "ui")):
        return "portal_upload", "Detected portal/web upload ingestion channel"

    if any(token in combined for token in ("api", "integration", "edi", "sftp")):
        return "system_integration", "Detected machine-to-machine integration source"

    if sender:
        return "email_attachment", "Inferred email source from sender metadata"

    return SOURCE_UNKNOWN, "Insufficient signals to determine PO source"
