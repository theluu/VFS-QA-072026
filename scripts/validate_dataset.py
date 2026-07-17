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
)
from validate_json import print_errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate manifest and annotation export together.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--annotations", required=True)
    parser.add_argument("--check-files", action="store_true")
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)
    annotation_path = Path(args.annotations)
    manifest = load_json(manifest_path)
    annotations = load_json(annotation_path)
    errors = validate_candidate_manifest(
        manifest,
        file=str(manifest_path),
        check_files=args.check_files,
        project_root=REPO_ROOT,
    )
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
    print("Dataset validation OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
