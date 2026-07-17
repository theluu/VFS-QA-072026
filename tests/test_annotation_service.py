from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from annotation_api.service import build_annotation_export
from scripts.validation_core import (
    REPO_ROOT,
    candidate_sample_ids,
    load_json,
    validate_annotation_export,
)


class AnnotationServiceTest(unittest.TestCase):
    def test_build_annotation_export_matches_schema(self) -> None:
        manifest = load_json(REPO_ROOT / "data" / "samples" / "candidate-manifest.sample.json")
        sample = manifest["samples"][0]
        export = build_annotation_export(
            dataset_id=manifest["dataset_id"],
            annotation_batch_id="unit-test-batch",
            annotations=[
                {
                    "sample_id": sample["sample_id"],
                    "event_label": "intrusion_crossing",
                    "event_start_ms": sample["start_ms"],
                    "event_end_ms": sample["end_ms"],
                    "ground_truth_status": "confirmed",
                    "reviewer": "unit_test",
                    "reviewed_at": "2026-07-17T00:00:00Z",
                    "comment": "Validated by unit test.",
                    "annotation_version": 1,
                }
            ],
        )
        self.assertEqual(
            validate_annotation_export(export, valid_sample_ids=candidate_sample_ids(manifest)),
            [],
        )


if __name__ == "__main__":
    unittest.main()
