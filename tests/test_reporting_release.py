from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.coverage_report import build_coverage_report
from scripts.release import main as release_main
from scripts.validation_core import (
    REPO_ROOT,
    load_json,
    validate_coverage_report,
    write_json,
)


class ReportingReleaseTest(unittest.TestCase):
    def test_build_coverage_report_validates(self) -> None:
        manifest = load_json(REPO_ROOT / "data" / "samples" / "candidate-manifest.sample.json")
        annotations = load_json(REPO_ROOT / "data" / "samples" / "annotation-export.sample.json")
        report = build_coverage_report(manifest, annotations)
        self.assertEqual(validate_coverage_report(report), [])
        self.assertEqual(report["summary"]["total_candidate_samples"], 2)
        self.assertEqual(report["summary"]["annotation_completion_rate"], 1.0)

    def test_release_script_creates_required_artifacts(self) -> None:
        manifest = REPO_ROOT / "data" / "samples" / "candidate-manifest.sample.json"
        annotations = REPO_ROOT / "data" / "samples" / "annotation-export.sample.json"
        coverage_data = build_coverage_report(load_json(manifest), load_json(annotations))
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            coverage = tmp_path / "coverage-report.json"
            output = tmp_path / "release"
            write_json(coverage, coverage_data)
            exit_code = release_main(
                [
                    "--manifest",
                    str(manifest),
                    "--annotations",
                    str(annotations),
                    "--coverage",
                    str(coverage),
                    "--output",
                    str(output),
                ]
            )
            self.assertEqual(exit_code, 0)
            expected = {
                "candidate-manifest.json",
                "annotation-export.json",
                "coverage-report.json",
                "dataset-card.md",
                "artifact-checklist.md",
                "release-notes.md",
                "checksums.sha256",
            }
            self.assertEqual(expected, {path.name for path in output.iterdir() if path.is_file()})


if __name__ == "__main__":
    unittest.main()
