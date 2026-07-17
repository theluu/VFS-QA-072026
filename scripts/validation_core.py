from __future__ import annotations

import json
import re
from pathlib import Path, PureWindowsPath
from typing import Any

SUPPORTED_SCHEMA_VERSION = "1.0.0"
REPO_ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str | Path, data: Any) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def make_error(
    code: str,
    message: str,
    *,
    file: str = "",
    sample_id: str = "",
    field: str = "",
    severity: str = "error",
    suggested_fix: str = "",
) -> dict[str, str]:
    return {
        "error_code": code,
        "severity": severity,
        "file": file,
        "sample_id": sample_id,
        "field": field,
        "message": message,
        "suggested_fix": suggested_fix,
    }


def load_label_config(path: str | Path | None = None) -> dict[str, Any]:
    config_path = Path(path) if path else REPO_ROOT / "configs" / "labels.json"
    data = load_json(config_path)
    labels = [item["value"] for item in data.get("event_labels", [])]
    statuses = data.get("ground_truth_statuses", [])
    return {"labels": labels, "statuses": statuses, "raw": data}


def is_relative_artifact_path(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    if value.startswith("~"):
        return False
    if Path(value).is_absolute():
        return False
    if PureWindowsPath(value).is_absolute():
        return False
    if re.match(r"^[A-Za-z]:[\\/]", value):
        return False
    return True


def validate_schema_document(path: str | Path) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    path = Path(path)
    try:
        data = load_json(path)
    except json.JSONDecodeError as exc:
        return [
            make_error(
                "SCHEMA_INVALID_JSON",
                f"Schema is not valid JSON: {exc}",
                file=str(path),
                suggested_fix="Fix JSON syntax.",
            )
        ]

    for field in ("$schema", "$id", "title", "version"):
        if field not in data:
            errors.append(
                make_error(
                    "SCHEMA_REQUIRED_FIELD_MISSING",
                    f"Schema missing required field {field}.",
                    file=str(path),
                    field=field,
                    suggested_fix=f"Add {field}.",
                )
            )
    if data.get("version") != SUPPORTED_SCHEMA_VERSION:
        errors.append(
            make_error(
                "SCHEMA_UNSUPPORTED_VERSION",
                f"Unsupported schema version {data.get('version')!r}.",
                file=str(path),
                field="version",
                suggested_fix=f"Use {SUPPORTED_SCHEMA_VERSION}.",
            )
        )
    return errors


def _require_fields(
    item: dict[str, Any],
    required: list[str],
    *,
    file: str,
    sample_id: str = "",
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    for field in required:
        if field not in item:
            errors.append(
                make_error(
                    "REQUIRED_FIELD_MISSING",
                    f"Missing required field {field}.",
                    file=file,
                    sample_id=sample_id,
                    field=field,
                    suggested_fix=f"Add {field}.",
                )
            )
    return errors


def validate_candidate_manifest(
    data: dict[str, Any],
    *,
    file: str = "",
    check_files: bool = False,
    project_root: Path = REPO_ROOT,
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    required = [
        "schema_version",
        "dataset_id",
        "manifest_id",
        "generated_at",
        "generator_version",
        "random_seed",
        "samples",
    ]
    errors.extend(_require_fields(data, required, file=file))
    if errors:
        return errors
    if data["schema_version"] != SUPPORTED_SCHEMA_VERSION:
        errors.append(
            make_error(
                "UNSUPPORTED_SCHEMA_VERSION",
                "Candidate manifest schema_version is not supported.",
                file=file,
                field="schema_version",
                suggested_fix=f"Use {SUPPORTED_SCHEMA_VERSION}.",
            )
        )
    if not isinstance(data["random_seed"], int):
        errors.append(
            make_error(
                "INVALID_RANDOM_SEED",
                "random_seed must be an integer.",
                file=file,
                field="random_seed",
            )
        )

    samples = data["samples"]
    if not isinstance(samples, list) or not samples:
        return errors + [
            make_error(
                "INVALID_SAMPLES",
                "samples must be a non-empty array.",
                file=file,
                field="samples",
            )
        ]

    seen: set[str] = set()
    sample_required = [
        "sample_id",
        "source_video_id",
        "source_video_path",
        "source_video_duration_ms",
        "clip_path",
        "clip_type",
        "candidate_rule",
        "start_ms",
        "end_ms",
        "duration_ms",
        "metadata",
    ]
    for index, sample in enumerate(samples):
        if not isinstance(sample, dict):
            errors.append(
                make_error(
                    "INVALID_SAMPLE",
                    "Each sample must be an object.",
                    file=file,
                    field=f"samples[{index}]",
                )
            )
            continue
        sample_id = str(sample.get("sample_id", ""))
        errors.extend(_require_fields(sample, sample_required, file=file, sample_id=sample_id))
        if not sample_id:
            errors.append(
                make_error(
                    "EMPTY_SAMPLE_ID",
                    "sample_id must not be empty.",
                    file=file,
                    sample_id=sample_id,
                    field="sample_id",
                )
            )
        elif sample_id in seen:
            errors.append(
                make_error(
                    "DUPLICATE_SAMPLE_ID",
                    f"Duplicate sample_id {sample_id}.",
                    file=file,
                    sample_id=sample_id,
                    field="sample_id",
                    suggested_fix="Regenerate sample IDs or fix duplicate windows.",
                )
            )
        seen.add(sample_id)
        if sample.get("clip_type") not in {"event", "background"}:
            errors.append(
                make_error(
                    "INVALID_CLIP_TYPE",
                    "clip_type must be event or background.",
                    file=file,
                    sample_id=sample_id,
                    field="clip_type",
                )
            )
        for field in ("source_video_path", "clip_path"):
            if not is_relative_artifact_path(sample.get(field)):
                errors.append(
                    make_error(
                        "ABSOLUTE_OR_EMPTY_PATH",
                        f"{field} must be a non-empty relative path.",
                        file=file,
                        sample_id=sample_id,
                        field=field,
                    )
                )
        start_ms = sample.get("start_ms")
        end_ms = sample.get("end_ms")
        duration_ms = sample.get("duration_ms")
        source_duration_ms = sample.get("source_video_duration_ms")
        numeric_fields = {
            "start_ms": start_ms,
            "end_ms": end_ms,
            "duration_ms": duration_ms,
            "source_video_duration_ms": source_duration_ms,
        }
        for field, value in numeric_fields.items():
            if not isinstance(value, int):
                errors.append(
                    make_error(
                        "INVALID_INTEGER_FIELD",
                        f"{field} must be an integer.",
                        file=file,
                        sample_id=sample_id,
                        field=field,
                    )
                )
        if all(isinstance(value, int) for value in numeric_fields.values()):
            if start_ms < 0:
                errors.append(
                    make_error(
                        "NEGATIVE_START_MS",
                        "start_ms must be >= 0.",
                        file=file,
                        sample_id=sample_id,
                        field="start_ms",
                    )
                )
            if end_ms <= start_ms:
                errors.append(
                    make_error(
                        "INVALID_TIME_RANGE",
                        "end_ms must be greater than start_ms.",
                        file=file,
                        sample_id=sample_id,
                        field="end_ms",
                    )
                )
            if duration_ms != end_ms - start_ms:
                errors.append(
                    make_error(
                        "INVALID_DURATION",
                        "duration_ms must equal end_ms - start_ms.",
                        file=file,
                        sample_id=sample_id,
                        field="duration_ms",
                    )
                )
            if end_ms > source_duration_ms:
                errors.append(
                    make_error(
                        "END_AFTER_SOURCE_DURATION",
                        "end_ms must not exceed source_video_duration_ms.",
                        file=file,
                        sample_id=sample_id,
                        field="end_ms",
                    )
                )
        if check_files:
            clip_path = project_root / str(sample.get("clip_path", ""))
            if not clip_path.exists():
                errors.append(
                    make_error(
                        "CLIP_PATH_MISSING",
                        "clip_path does not exist.",
                        file=file,
                        sample_id=sample_id,
                        field="clip_path",
                        suggested_fix="Regenerate clips or fix manifest path.",
                    )
                )
    return errors


def validate_annotation_export(
    data: dict[str, Any],
    *,
    file: str = "",
    valid_sample_ids: set[str] | None = None,
    label_config: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    label_config = label_config or load_label_config()
    labels = set(label_config["labels"])
    statuses = set(label_config["statuses"])
    required = [
        "schema_version",
        "dataset_id",
        "annotation_batch_id",
        "exported_at",
        "annotations",
    ]
    errors.extend(_require_fields(data, required, file=file))
    if errors:
        return errors
    if data["schema_version"] != SUPPORTED_SCHEMA_VERSION:
        errors.append(
            make_error(
                "UNSUPPORTED_SCHEMA_VERSION",
                "Annotation export schema_version is not supported.",
                file=file,
                field="schema_version",
            )
        )

    annotations = data["annotations"]
    if not isinstance(annotations, list):
        return errors + [
            make_error(
                "INVALID_ANNOTATIONS",
                "annotations must be an array.",
                file=file,
                field="annotations",
            )
        ]

    seen: set[str] = set()
    annotation_required = [
        "sample_id",
        "event_label",
        "event_start_ms",
        "event_end_ms",
        "ground_truth_status",
        "reviewer",
        "reviewed_at",
        "comment",
        "annotation_version",
    ]
    for index, annotation in enumerate(annotations):
        if not isinstance(annotation, dict):
            errors.append(
                make_error(
                    "INVALID_ANNOTATION",
                    "Each annotation must be an object.",
                    file=file,
                    field=f"annotations[{index}]",
                )
            )
            continue
        sample_id = str(annotation.get("sample_id", ""))
        errors.extend(_require_fields(annotation, annotation_required, file=file, sample_id=sample_id))
        if not sample_id:
            errors.append(
                make_error(
                    "EMPTY_SAMPLE_ID",
                    "sample_id must not be empty.",
                    file=file,
                    sample_id=sample_id,
                    field="sample_id",
                )
            )
        elif sample_id in seen:
            errors.append(
                make_error(
                    "DUPLICATE_ANNOTATION",
                    "Only one active annotation per sample is allowed in one export.",
                    file=file,
                    sample_id=sample_id,
                    field="sample_id",
                )
            )
        seen.add(sample_id)
        if valid_sample_ids is not None and sample_id not in valid_sample_ids:
            errors.append(
                make_error(
                    "ORPHAN_ANNOTATION",
                    "Annotation references a sample_id that does not exist in manifest.",
                    file=file,
                    sample_id=sample_id,
                    field="sample_id",
                )
            )
        if annotation.get("event_label") not in labels:
            errors.append(
                make_error(
                    "INVALID_EVENT_LABEL",
                    "event_label is not configured in configs/labels.json.",
                    file=file,
                    sample_id=sample_id,
                    field="event_label",
                )
            )
        status = annotation.get("ground_truth_status")
        if status not in statuses:
            errors.append(
                make_error(
                    "INVALID_GROUND_TRUTH_STATUS",
                    "ground_truth_status is not configured.",
                    file=file,
                    sample_id=sample_id,
                    field="ground_truth_status",
                )
            )
        start_ms = annotation.get("event_start_ms")
        end_ms = annotation.get("event_end_ms")
        if not isinstance(start_ms, int) or not isinstance(end_ms, int):
            errors.append(
                make_error(
                    "INVALID_ANNOTATION_TIMESTAMP",
                    "event_start_ms and event_end_ms must be integer milliseconds.",
                    file=file,
                    sample_id=sample_id,
                    field="event_start_ms",
                )
            )
        elif start_ms < 0 or end_ms <= start_ms:
            errors.append(
                make_error(
                    "INVALID_ANNOTATION_TIME_RANGE",
                    "event_end_ms must be greater than event_start_ms and start must be >= 0.",
                    file=file,
                    sample_id=sample_id,
                    field="event_end_ms",
                )
            )
        if status == "confirmed" and not str(annotation.get("reviewer", "")).strip():
            errors.append(
                make_error(
                    "REVIEWER_REQUIRED",
                    "reviewer is required when ground_truth_status is confirmed.",
                    file=file,
                    sample_id=sample_id,
                    field="reviewer",
                )
            )
        if not isinstance(annotation.get("annotation_version"), int) or annotation.get("annotation_version", 0) < 1:
            errors.append(
                make_error(
                    "INVALID_ANNOTATION_VERSION",
                    "annotation_version must be an integer >= 1.",
                    file=file,
                    sample_id=sample_id,
                    field="annotation_version",
                )
            )
    return errors


def validate_coverage_report(data: dict[str, Any], *, file: str = "") -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    required = [
        "schema_version",
        "dataset_id",
        "report_id",
        "generated_at",
        "summary",
        "by_event_label",
        "by_source_video",
    ]
    errors.extend(_require_fields(data, required, file=file))
    if errors:
        return errors
    if data["schema_version"] != SUPPORTED_SCHEMA_VERSION:
        errors.append(
            make_error(
                "UNSUPPORTED_SCHEMA_VERSION",
                "Coverage report schema_version is not supported.",
                file=file,
                field="schema_version",
            )
        )
    summary = data.get("summary")
    if not isinstance(summary, dict):
        return errors + [
            make_error(
                "INVALID_SUMMARY",
                "summary must be an object.",
                file=file,
                field="summary",
            )
        ]
    required_summary = [
        "total_videos",
        "total_duration_ms",
        "total_candidate_samples",
        "event_samples",
        "background_samples",
        "reviewed_samples",
        "unreviewed_samples",
        "confirmed_samples",
        "rejected_samples",
        "needs_review_samples",
        "annotation_completion_rate",
        "confirmed_rate",
        "valid_artifact_rate",
    ]
    errors.extend(_require_fields(summary, required_summary, file=file))
    for field in required_summary:
        value = summary.get(field)
        if field.endswith("_rate"):
            if not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
                errors.append(
                    make_error(
                        "INVALID_RATE",
                        f"{field} must be a number between 0 and 1.",
                        file=file,
                        field=f"summary.{field}",
                    )
                )
        elif not isinstance(value, int) or value < 0:
            errors.append(
                make_error(
                    "INVALID_COUNT",
                    f"{field} must be a non-negative integer.",
                    file=file,
                    field=f"summary.{field}",
                )
            )
    return errors


def candidate_sample_ids(manifest: dict[str, Any]) -> set[str]:
    return {str(sample.get("sample_id", "")) for sample in manifest.get("samples", [])}
