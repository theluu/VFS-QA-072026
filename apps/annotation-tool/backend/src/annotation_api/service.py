from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.validation_core import (
    REPO_ROOT,
    candidate_sample_ids,
    load_json,
    validate_annotation_export,
    validate_candidate_manifest,
    write_json,
)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_repo_path(relative_path: str) -> Path:
    if not relative_path or Path(relative_path).is_absolute() or re.match(r"^[A-Za-z]:[\\/]", relative_path):
        raise ValueError("Path must be relative to repository root")
    resolved = (REPO_ROOT / relative_path).resolve()
    resolved.relative_to(REPO_ROOT)
    return resolved


def load_config() -> dict[str, Any]:
    return load_json(REPO_ROOT / "configs" / "labels.json")


def load_manifest(relative_path: str) -> dict[str, Any]:
    manifest_path = safe_repo_path(relative_path)
    manifest = load_json(manifest_path)
    errors = validate_candidate_manifest(manifest, file=relative_path)
    if errors:
        raise ValueError(f"Manifest validation failed: {errors[0]['message']}")
    return manifest


def validate_manifest_payload(payload: dict[str, Any]) -> list[dict[str, str]]:
    return validate_candidate_manifest(payload, file="<request>")


def build_annotation_export(
    *,
    dataset_id: str,
    annotation_batch_id: str,
    annotations: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "dataset_id": dataset_id,
        "annotation_batch_id": annotation_batch_id,
        "exported_at": utc_now(),
        "annotations": annotations,
    }


def export_annotations(
    *,
    manifest_path: str,
    annotation_batch_id: str,
    annotations: list[dict[str, Any]],
    output_path: str | None = None,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    export = build_annotation_export(
        dataset_id=manifest["dataset_id"],
        annotation_batch_id=annotation_batch_id,
        annotations=annotations,
    )
    errors = validate_annotation_export(
        export,
        file=output_path or "<export>",
        valid_sample_ids=candidate_sample_ids(manifest),
    )
    if errors:
        return {"ok": False, "errors": errors, "export": export}

    safe_batch_id = re.sub(r"[^A-Za-z0-9_.-]+", "-", annotation_batch_id).strip("-")
    if not safe_batch_id:
        safe_batch_id = "annotation-export"
    relative_output = output_path or f"outputs/annotations/{safe_batch_id}.json"
    output = safe_repo_path(relative_output)
    write_json(output, export)
    return {
        "ok": True,
        "errors": [],
        "export": export,
        "output_path": output.relative_to(REPO_ROOT).as_posix(),
    }
