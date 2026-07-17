from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

from validation_core import load_json


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a local release package.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--annotations", required=True)
    parser.add_argument("--coverage", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "candidate-manifest.json": Path(args.manifest),
        "annotation-export.json": Path(args.annotations),
        "coverage-report.json": Path(args.coverage),
    }
    for name, source in files.items():
        if not source.exists():
            print(f"Missing release input: {source}")
            return 1
        shutil.copy2(source, output_dir / name)

    manifest = load_json(args.manifest)
    coverage = load_json(args.coverage)
    dataset_card = f"""# Dataset Card

## Dataset Name

{manifest.get("dataset_id", "unknown")}

## Dataset Version

v0.1.0

## Purpose

Candidate review and annotation POC for AI Camera test data preparation.

## Candidate Generation Rules

See candidate manifest `generator_version` and sample `candidate_rule` fields.

## Coverage

- Total samples: {coverage.get("summary", {}).get("total_candidate_samples", 0)}
- Reviewed samples: {coverage.get("summary", {}).get("reviewed_samples", 0)}
- Completion rate: {coverage.get("summary", {}).get("annotation_completion_rate", 0)}

## Privacy Considerations

Do not publish raw camera video or annotations containing personal data without approval.
"""
    write_text(output_dir / "dataset-card.md", dataset_card)
    write_text(
        output_dir / "artifact-checklist.md",
        "# Artifact Checklist\n\n- [x] Candidate manifest\n- [x] Annotation export\n- [x] Coverage report\n- [x] Dataset card\n",
    )
    write_text(
        output_dir / "release-notes.md",
        "# Release Notes\n\nLocal POC release generated from validated manifest, annotations and coverage report.\n",
    )

    checksum_lines = []
    for path in sorted(output_dir.iterdir()):
        if path.name == "checksums.sha256" or not path.is_file():
            continue
        checksum_lines.append(f"{sha256_file(path)}  {path.name}")
    write_text(output_dir / "checksums.sha256", "\n".join(checksum_lines) + "\n")
    print(f"Wrote release package to {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
