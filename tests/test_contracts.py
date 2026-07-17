from __future__ import annotations

import unittest
from pathlib import Path

from scripts.validation_core import (
    REPO_ROOT,
    candidate_sample_ids,
    load_json,
    validate_annotation_export,
    validate_candidate_manifest,
    validate_coverage_report,
    validate_schema_document,
)


class ContractValidationTest(unittest.TestCase):
    def test_schema_documents_have_required_metadata(self) -> None:
        schema_dir = REPO_ROOT / "shared" / "schemas"
        for path in schema_dir.glob("*.schema.json"):
            with self.subTest(path=path.name):
                self.assertEqual(validate_schema_document(path), [])

    def test_sample_manifest_annotation_and_coverage_are_valid(self) -> None:
        manifest = load_json(REPO_ROOT / "data" / "samples" / "candidate-manifest.sample.json")
        annotations = load_json(REPO_ROOT / "data" / "samples" / "annotation-export.sample.json")
        coverage = load_json(REPO_ROOT / "data" / "samples" / "coverage-report.sample.json")

        self.assertEqual(validate_candidate_manifest(manifest), [])
        self.assertEqual(
            validate_annotation_export(annotations, valid_sample_ids=candidate_sample_ids(manifest)),
            [],
        )
        self.assertEqual(validate_coverage_report(coverage), [])

    def test_invalid_candidate_fixtures_are_rejected(self) -> None:
        for name in ("candidate-duplicate-sample-id.json", "candidate-bad-timestamp.json"):
            path = REPO_ROOT / "tests" / "fixtures" / "invalid" / name
            with self.subTest(name=name):
                errors = validate_candidate_manifest(load_json(path), file=name)
                self.assertGreater(len(errors), 0)

    def test_invalid_annotation_fixtures_are_rejected(self) -> None:
        manifest = load_json(REPO_ROOT / "data" / "samples" / "candidate-manifest.sample.json")
        valid_ids = candidate_sample_ids(manifest)
        for name in ("annotation-orphan.json", "annotation-bad-label.json"):
            path = REPO_ROOT / "tests" / "fixtures" / "invalid" / name
            with self.subTest(name=name):
                errors = validate_annotation_export(load_json(path), file=name, valid_sample_ids=valid_ids)
                self.assertGreater(len(errors), 0)


if __name__ == "__main__":
    unittest.main()
