from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from src.pipeline import run_phase1_step6


def _load_payload(input_path: str | None) -> dict[str, Any]:
    if input_path:
        return json.loads(Path(input_path).read_text(encoding="utf-8"))

    raw = sys.stdin.read().strip()
    if not raw:
        raise ValueError("No input provided. Pass --input <file.json> or pipe JSON via stdin.")
    return json.loads(raw)


def main() -> None:
    parser = argparse.ArgumentParser(description="PO triage phase-1 step runner")
    parser.add_argument("--input", help="Path to JSON input payload")
    args = parser.parse_args()

    payload = _load_payload(args.input)
    output = run_phase1_step6(payload)

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
