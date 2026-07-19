from __future__ import annotations

import unittest
import warnings
from pathlib import Path
from unittest.mock import patch

try:
    warnings.filterwarnings(
        "ignore",
        message="Using `httpx` with `starlette.testclient` is deprecated.*",
    )
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="fastapi.testclient")
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="starlette.testclient")
    from fastapi.testclient import TestClient

    from annotation_api import app as app_module
    from annotation_api.app import app
    from scripts.validation_core import REPO_ROOT
except Exception:  # pragma: no cover - dependency may not be installed before make setup
    TestClient = None
    app = None


@unittest.skipIf(TestClient is None, "FastAPI TestClient is not installed")
class AnnotationApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self._set_triage_report(None)

    def _set_triage_report(self, report: dict | None) -> None:
        with app_module._triage_lock:
            app_module._triage_state.update(
                status="idle",
                report=report,
                report_path="",
                processed=0,
                total=0,
                current="",
                error="",
                frame_done=0,
                frame_total=0,
                percent=0,
            )

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

    def test_triage_mine_requires_finished_detection_report(self) -> None:
        self._set_triage_report(None)
        response = self.client.post("/triage/mine", json={})
        self.assertEqual(response.status_code, 400)

    def test_triage_mine_uses_kept_report_entry(self) -> None:
        video_path = Path("outputs/api-triage-input.mp4")
        video_path.parent.mkdir(parents=True, exist_ok=True)
        video_path.write_bytes(b"fixture")
        self.addCleanup(lambda: video_path.unlink(missing_ok=True))
        self._set_triage_report(
            {
                "schema_version": "1.0.0",
                "detector": "unit-detector",
                "settings": {"sample_interval_ms": 1000},
                "videos": [
                    {
                        "video_path": video_path.as_posix(),
                        "decision": "keep",
                        "person_timestamps_ms": [1000, 2000],
                        "hits": [{"timestamp_ms": 1000, "confidence": 0.9}],
                    }
                ],
                "kept": [video_path.as_posix()],
                "rejected": [],
            }
        )

        def fake_mine(**kwargs):
            self.assertEqual(kwargs["video_path"], REPO_ROOT / video_path)
            self.assertEqual(kwargs["detection_entry"]["detector"], "unit-detector")
            self.assertEqual(kwargs["output_dir"], REPO_ROOT / "outputs" / "runs" / "api-triage-input")
            return {
                "source_video_id": "unit",
                "video_path": video_path.as_posix(),
                "run_dir": "outputs/runs/api-triage-input",
                "inventory_path": "outputs/runs/api-triage-input/inventory.json",
                "manifest_path": "outputs/runs/api-triage-input/candidate-manifest.json",
                "summary_path": "outputs/runs/api-triage-input/run-summary.json",
                "log_path": "outputs/runs/api-triage-input/processing.log",
                "event_count": 1,
                "background_count": 0,
                "sample_count": 1,
            }

        with patch("candidate_mining.detected.mine_person_detection_video", side_effect=fake_mine):
            response = self.client.post("/triage/mine", json={"videos": [video_path.as_posix()]})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(
            payload["outputs"][0]["manifest_path"],
            "outputs/runs/api-triage-input/candidate-manifest.json",
        )

    def test_triage_bbox_renders_relative_raw_video(self) -> None:
        video_path = Path("outputs/api-bbox-input.mp4")
        video_path.parent.mkdir(parents=True, exist_ok=True)
        video_path.write_bytes(b"fixture")
        self.addCleanup(lambda: video_path.unlink(missing_ok=True))

        def fake_render(**kwargs):
            self.assertEqual(kwargs["input_path"], REPO_ROOT / video_path)
            self.assertEqual(kwargs["model"], "yolov4")
            self.assertEqual(kwargs["sample_fps"], 5.0)
            self.assertEqual(kwargs["min_confidence"], 0.3)
            return {
                "output_path": "outputs/annotated/api-bbox-input_person_detected-0001_0.0s-1.0s_bbox.mp4",
                "frame_count": 30,
                "source_frame_count": 30,
                "duration_ms": 1000,
                "distinct_people": 1,
                "model": "yolov4",
                "sample_fps": 5.0,
                "min_confidence": 0.3,
            }

        with patch("candidate_mining.bbox_video.render_person_bbox_video", side_effect=fake_render):
            response = self.client.post(
                "/triage/bbox",
                json={
                    "path": video_path.as_posix(),
                    "model": "yolov4",
                    "sample_fps": 5,
                    "min_confidence": 0.3,
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["result"]["output_path"].endswith("_bbox.mp4"))


if __name__ == "__main__":
    unittest.main()
