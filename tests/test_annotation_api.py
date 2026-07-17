from __future__ import annotations

import unittest
import warnings
from pathlib import Path

try:
    warnings.filterwarnings(
        "ignore",
        message="Using `httpx` with `starlette.testclient` is deprecated.*",
    )
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="fastapi.testclient")
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="starlette.testclient")
    from fastapi.testclient import TestClient

    from annotation_api.app import app
except Exception:  # pragma: no cover - dependency may not be installed before make setup
    TestClient = None
    app = None


@unittest.skipIf(TestClient is None, "FastAPI TestClient is not installed")
class AnnotationApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health_config_and_manifest_endpoints(self) -> None:
        health = self.client.get("/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["version"], "0.1.0")

        config = self.client.get("/config")
        self.assertEqual(config.status_code, 200)
        self.assertGreater(len(config.json()["event_labels"]), 0)

        manifest = self.client.get(
            "/manifest",
            params={"path": "data/samples/candidate-manifest.sample.json"},
        )
        self.assertEqual(manifest.status_code, 200)
        self.assertEqual(manifest.json()["manifest"]["dataset_id"], "sample-dataset")

    def test_export_endpoint_rejects_invalid_annotation(self) -> None:
        response = self.client.post(
            "/annotations/export",
            json={
                "manifest_path": "data/samples/candidate-manifest.sample.json",
                "annotation_batch_id": "api-invalid",
                "annotations": [
                    {
                        "sample_id": "missing",
                        "event_label": "not_configured",
                        "event_start_ms": 0,
                        "event_end_ms": 1000,
                        "ground_truth_status": "confirmed",
                        "reviewer": "",
                        "reviewed_at": "2026-07-17T00:00:00Z",
                        "comment": "",
                        "annotation_version": 1,
                    }
                ],
            },
        )
        self.assertEqual(response.status_code, 422)
        error_codes = {item["error_code"] for item in response.json()["detail"]}
        self.assertIn("ORPHAN_ANNOTATION", error_codes)
        self.assertIn("INVALID_EVENT_LABEL", error_codes)
        self.assertIn("REVIEWER_REQUIRED", error_codes)

    def test_export_endpoint_writes_valid_annotation(self) -> None:
        output_path = Path("outputs/annotations/api-unit-test.json")
        if output_path.exists():
            output_path.unlink()
        response = self.client.post(
            "/annotations/export",
            json={
                "manifest_path": "data/samples/candidate-manifest.sample.json",
                "annotation_batch_id": "api-unit-test",
                "output_path": output_path.as_posix(),
                "annotations": [
                    {
                        "sample_id": "samplevideo01__15000__82000__intrusion_manual_v1",
                        "event_label": "intrusion_crossing",
                        "event_start_ms": 45500,
                        "event_end_ms": 52000,
                        "ground_truth_status": "confirmed",
                        "reviewer": "api_test",
                        "reviewed_at": "2026-07-17T00:00:00Z",
                        "comment": "API integration test.",
                        "annotation_version": 1,
                    }
                ],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        self.assertTrue(output_path.exists())
        output_path.unlink()


if __name__ == "__main__":
    unittest.main()
