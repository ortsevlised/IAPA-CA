# PO Triage

## Scope (Phase 1)

- Classify incoming PO format/source
- Check duplicates
- Extract structured fields (template path + AI/OCR stub path)
- Validate extraction confidence
- Score priority using DMN-equivalent logic
- Emit JSON output for downstream automation

## Simple Flow

```mermaid
flowchart LR
    A[Incoming PO] --> B[Classify Format/Source]
    B --> C[Duplicate Check]
    C --> D[Extract Fields]
    D --> E[Validate Confidence]
    E --> F[Priority Scoring]
    F --> G[JSON Output]
```

## Reference Diagrams

### As-Is Process

![As-Is Process](as_is.png)

### To-Be Process

![To-Be Process](to_be.png)

## Planned Module Layout

- `src/main.py` - JSON-first CLI entrypoint
- `src/pipeline.py` - orchestrator
- `src/classifier.py`
- `src/duplicate_checker.py`
- `src/template_extractor.py`
- `src/ai_extractor.py`
- `src/validator.py`
- `src/priority_scorer.py`

## Setup (uv)

```bash
uv sync
```

## Run
