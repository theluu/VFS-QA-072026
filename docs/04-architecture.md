# Architecture

```text
Raw Video
    |
    v
Video Inventory
    |
    v
Candidate Mining
    |
    +----> Event Proxy Clips
    |
    +----> Random Background Clips
    |
    v
Candidate Manifest
    |
    v
Annotation Tool
    |
    v
Annotation Export
    |
    +----> Dataset Validator
    |
    +----> Coverage Report
    |
    +----> Dataset Card
```

## Components

- Candidate mining CLI: video metadata, boundary, clip generation, manifest.
- FastAPI backend: load config, validate manifest/export, serve clips, optional LLM note.
- React UI: review queue, clip viewer, annotation form, export.
- Scripts: schema validation, dataset validation, coverage, release.

## Failure Handling

- Invalid video path: fail before writing manifest.
- Invalid timestamp: reject event.
- Missing clip: validation error.
- Invalid annotation: reject export.

## Storage

- Raw input in `data/raw/`.
- Generated run output in `outputs/runs/{run_id}/`.
- Annotation export in `outputs/annotations/`.

## Logging

Candidate mining writes `processing.log` and `run-summary.json`.

## Configuration

Labels and statuses are loaded from `configs/labels.json`.

## Test Boundary

Unit tests cover deterministic logic and validation. Real video integration requires a safe video fixture.
