from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

from validation_core import (
    candidate_sample_ids,
    load_json,
    validate_annotation_export,
    validate_candidate_manifest,
    validate_coverage_report,
    write_json,
)
from validate_json import print_errors


def rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 6)


def build_coverage_report(manifest: dict, annotations: dict) -> dict:
    samples = manifest.get("samples", [])
    annotation_items = annotations.get("annotations", [])
    reviewed_statuses = {"confirmed", "rejected", "needs_review"}
    reviewed = [
        item for item in annotation_items if item.get("ground_truth_status") in reviewed_statuses
    ]
    status_counts = Counter(item.get("ground_truth_status") for item in annotation_items)
    by_label = Counter(item.get("event_label") for item in annotation_items if item.get("event_label"))
    by_source: dict[str, dict[str, int]] = defaultdict(lambda: {"samples": 0, "duration_ms": 0})
    source_duration_seen: dict[str, int] = {}
    for sample in samples:
        source_id = sample["source_video_id"]
        by_source[source_id]["samples"] += 1
        source_duration_seen[source_id] = max(
            source_duration_seen.get(source_id, 0),
            sample.get("source_video_duration_ms", 0),
        )
    for source_id, duration in source_duration_seen.items():
        by_source[source_id]["duration_ms"] = duration

    total_samples = len(samples)
    reviewed_count = len(reviewed)
    report = {
        "schema_version": "1.0.0",
        "dataset_id": manifest["dataset_id"],
        "report_id": f"coverage-{manifest['manifest_id']}",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "summary": {
            "total_videos": len(by_source),
            "total_duration_ms": sum(source_duration_seen.values()),
            "total_candidate_samples": total_samples,
            "event_samples": sum(1 for sample in samples if sample.get("clip_type") == "event"),
            "background_samples": sum(1 for sample in samples if sample.get("clip_type") == "background"),
            "reviewed_samples": reviewed_count,
            "unreviewed_samples": max(total_samples - reviewed_count, 0),
            "confirmed_samples": status_counts["confirmed"],
            "rejected_samples": status_counts["rejected"],
            "needs_review_samples": status_counts["needs_review"],
            "annotation_completion_rate": rate(reviewed_count, total_samples),
            "confirmed_rate": rate(status_counts["confirmed"], reviewed_count),
            "valid_artifact_rate": 1.0,
        },
        "by_event_label": dict(sorted(by_label.items())),
        "by_source_video": dict(sorted(by_source.items())),
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate coverage report.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--annotations", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)
    annotation_path = Path(args.annotations)
    manifest = load_json(manifest_path)
    annotations = load_json(annotation_path)
    errors = validate_candidate_manifest(manifest, file=str(manifest_path))
    errors.extend(
        validate_annotation_export(
            annotations,
            file=str(annotation_path),
            valid_sample_ids=candidate_sample_ids(manifest),
        )
    )
    if errors:
        print_errors(errors)
        return 1
    report = build_coverage_report(manifest, annotations)
    report_errors = validate_coverage_report(report, file=args.output)
    if report_errors:
        print_errors(report_errors)
        return 1
    write_json(args.output, report)
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
