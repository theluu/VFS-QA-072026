from __future__ import annotations

import argparse
import sys
from pathlib import Path

from validation_core import (
    REPO_ROOT,
    candidate_sample_ids,
    load_json,
    validate_annotation_export,
    validate_candidate_manifest,
    validate_coverage_report,
    validate_schema_document,
)


def print_errors(errors: list[dict[str, str]]) -> None:
    for error in errors:
        location = error.get("file", "")
        sample_id = error.get("sample_id", "")
        field = error.get("field", "")
        parts = [error["error_code"]]
        if location:
            parts.append(location)
        if sample_id:
            parts.append(sample_id)
        if field:
            parts.append(field)
        print(" | ".join(parts) + f": {error['message']}")


def validate_schemas() -> int:
    errors: list[dict[str, str]] = []
    for path in sorted((REPO_ROOT / "shared" / "schemas").glob("*.schema.json")):
        errors.extend(validate_schema_document(path))
    if errors:
        print_errors(errors)
        return 1
    print("Schema documents OK")
    return 0


def validate_samples() -> int:
    errors: list[dict[str, str]] = []
    manifest_path = REPO_ROOT / "data" / "samples" / "candidate-manifest.sample.json"
    annotation_path = REPO_ROOT / "data" / "samples" / "annotation-export.sample.json"
    coverage_path = REPO_ROOT / "data" / "samples" / "coverage-report.sample.json"

    manifest = load_json(manifest_path)
    annotations = load_json(annotation_path)
    coverage = load_json(coverage_path)
    sample_ids = candidate_sample_ids(manifest)

    errors.extend(validate_candidate_manifest(manifest, file=str(manifest_path.relative_to(REPO_ROOT))))
    errors.extend(
        validate_annotation_export(
            annotations,
            file=str(annotation_path.relative_to(REPO_ROOT)),
            valid_sample_ids=sample_ids,
        )
    )
    errors.extend(validate_coverage_report(coverage, file=str(coverage_path.relative_to(REPO_ROOT))))

    invalid_failures: list[str] = []
    for path in sorted((REPO_ROOT / "tests" / "fixtures" / "invalid").glob("*.json")):
        data = load_json(path)
        if path.name.startswith("candidate-"):
            invalid_errors = validate_candidate_manifest(data, file=str(path.relative_to(REPO_ROOT)))
        elif path.name.startswith("annotation-"):
            invalid_errors = validate_annotation_export(
                data,
                file=str(path.relative_to(REPO_ROOT)),
                valid_sample_ids=sample_ids,
            )
        else:
            invalid_errors = []
        if not invalid_errors:
            invalid_failures.append(str(path.relative_to(REPO_ROOT)))

    if invalid_failures:
        for path in invalid_failures:
            print(f"INVALID_FIXTURE_ACCEPTED | {path}: invalid fixture passed validation")
        return 1
    if errors:
        print_errors(errors)
        return 1
    print("Sample JSON and invalid fixtures OK")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate schemas and sample JSON files.")
    parser.add_argument("--schemas", action="store_true", help="Validate schema documents.")
    parser.add_argument("--samples", action="store_true", help="Validate sample and invalid fixture JSON.")
    args = parser.parse_args(argv)

    if not args.schemas and not args.samples:
        parser.error("Use --schemas and/or --samples")

    exit_code = 0
    if args.schemas:
        exit_code = max(exit_code, validate_schemas())
    if args.samples:
        exit_code = max(exit_code, validate_samples())
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
