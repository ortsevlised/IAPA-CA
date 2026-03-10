from __future__ import annotations

import argparse
import json
import re
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping

from .pipeline import run_phase1_step6

WEB_ROOT = Path(__file__).resolve().parent.parent / "webui"
DEFAULT_MOCK_SF_RECORDS = [
    {"po_number": "PO-123", "customer_id": "CUST-1"},
    {"po_number": "PO-777", "customer_id": "CUST-77"},
]


def process_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return run_phase1_step6(_normalize_payload(payload))


def _normalize_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    document = normalized.pop("document", None)
    if isinstance(document, Mapping):
        normalized["filename"] = normalized.get("filename") or document.get("filename")
        normalized["mime_type"] = normalized.get("mime_type") or document.get("mime_type")
        normalized["text"] = normalized.get("text") or document.get("text") or ""
    text = str(normalized.get("text", ""))

    if not normalized.get("po_number"):
        normalized["po_number"] = _search(text, r"\bPO[-\s]?\d{2,}\b")
    if not normalized.get("customer_id"):
        normalized["customer_id"] = _search(text, r"\bCUST[-\s]?\d{1,}\b")

    normalized["source"] = normalized.get("source") or "portal_upload"
    normalized["template_id"] = normalized.get("template_id") or _infer_template_id(normalized.get("filename"))
    normalized["validation_threshold"] = float(normalized.get("validation_threshold", 0.7))

    if "is_expedited" not in normalized:
        normalized["is_expedited"] = "expedite" in str(normalized.get("text", "")).lower()
    if "is_month_end" not in normalized:
        text = str(normalized.get("text", "")).lower()
        normalized["is_month_end"] = "month-end" in text or "quarter-end" in text
    if "region" not in normalized:
        inferred_region = _infer_region_from_text(str(normalized.get("text", "")))
        if inferred_region:
            normalized["region"] = inferred_region

    existing_records = normalized.get("existing_records")
    if not isinstance(existing_records, list) or not existing_records:
        normalized["existing_records"] = list(DEFAULT_MOCK_SF_RECORDS)

    filename = str(normalized.get("filename", "")).lower()
    if "ai_stub_confidence" not in normalized:
        if "lowconf" in filename:
            normalized["ai_stub_confidence"] = 0.55
        elif "highconf" in filename:
            normalized["ai_stub_confidence"] = 0.92
    return normalized


def _infer_template_id(filename: Any) -> str:
    name = str(filename or "").lower()
    if "distributor" in name:
        return "distributor_v1"
    if "reseller" in name:
        return "reseller_standard_v2"
    return "unknown_layout"


def _search(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(0) if match else None


def _infer_region_from_text(text: str) -> str | None:
    lowered = text.lower()
    if "apac" in lowered:
        return "APAC"
    if "emea" in lowered:
        return "EMEA"
    if "usa" in lowered or "united states" in lowered:
        return "USA"
    return None


class TriageRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/triage":
            self._write_json(HTTPStatus.NOT_FOUND, {"error": "Route not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)
            payload = json.loads(raw.decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("Expected JSON object")
            output = process_payload(payload)
            self._write_json(HTTPStatus.OK, output)
        except Exception as exc:  # broad for endpoint safety
            self._write_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/health":
            self._write_json(HTTPStatus.OK, {"status": "ok"})
            return
        super().do_GET()

    def _write_json(self, status: HTTPStatus, body: dict[str, Any]) -> None:
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main() -> None:
    parser = argparse.ArgumentParser(description="PO triage web UI server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), TriageRequestHandler)
    print(f"PO Triage UI running at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
