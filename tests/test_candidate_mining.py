from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from candidate_mining.core import (
    TimeWindow,
    clamp_event_window,
    make_sample_id,
    sample_background_windows,
    stable_source_video_id,
    windows_overlap,
)
from candidate_mining.bbox_video import bbox_output_name
from candidate_mining.detected import detection_windows_from_timestamps, mine_person_detection_video
from scripts.validation_core import load_json, validate_candidate_manifest


class CandidateMiningCoreTest(unittest.TestCase):
    def test_clamp_event_window_uses_30_second_padding(self) -> None:
        window = clamp_event_window(45_000, 52_000, 120_000, padding_ms=30_000)
        self.assertEqual(window.start_ms, 15_000)
        self.assertEqual(window.end_ms, 82_000)
        self.assertEqual(window.duration_ms, 67_000)

    def test_clamp_event_window_does_not_go_negative(self) -> None:
        window = clamp_event_window(5_000, 8_000, 120_000, padding_ms=30_000)
        self.assertEqual(window.start_ms, 0)
        self.assertEqual(window.end_ms, 38_000)

    def test_sample_id_is_deterministic(self) -> None:
        source_id = stable_source_video_id("data/raw/sample.mp4", 120_000, 1024)
        self.assertEqual(source_id, stable_source_video_id("data/raw/sample.mp4", 120_000, 1024))
        self.assertEqual(
            make_sample_id(source_id, 15_000, 82_000, "intrusion_manual_v1"),
            f"{source_id}__15000__82000__intrusion_manual_v1",
        )

    def test_background_sampling_is_reproducible_and_excludes_events(self) -> None:
        exclusions = [TimeWindow(15_000, 82_000)]
        left = sample_background_windows(
            120_000,
            exclusions,
            count=2,
            window_ms=10_000,
            random_seed=7,
        )
        right = sample_background_windows(
            120_000,
            exclusions,
            count=2,
            window_ms=10_000,
            random_seed=7,
        )
        self.assertEqual(left, right)
        self.assertEqual(len(left), 2)
        for window in left:
            self.assertFalse(any(windows_overlap(window, blocked) for blocked in exclusions))

    def test_detection_windows_merge_after_padding(self) -> None:
        windows = detection_windows_from_timestamps(
            [12_000, 16_000, 29_000, 32_000],
            merge_gap_ms=3_000,
            padding_ms=30_000,
            duration_ms=41_967,
        )
        self.assertEqual(windows, [TimeWindow(0, 41_967)])

    def test_bbox_output_name_matches_reference_style(self) -> None:
        self.assertEqual(
            bbox_output_name("data/raw/VIRAT_S_000200_01_000226_000268.mp4", 41_967),
            "VIRAT_S_000200_01_000226_000268_person_detected-0001_0.0s-42.0s_bbox.mp4",
        )

    def test_mine_person_detection_video_writes_current_flow_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            video = project_root / "data" / "raw" / "demo.mp4"
            output_dir = project_root / "outputs" / "runs" / "demo"
            video.parent.mkdir(parents=True)
            video.write_bytes(b"fixture video")

            def fake_cut(_input: Path, output: Path, _start_ms: int, _end_ms: int) -> None:
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(b"clip")

            with (
                patch(
                    "candidate_mining.detected.probe_video",
                    return_value={
                        "duration_ms": 120_000,
                        "file_size": 1024,
                        "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
                        "codec_name": "h264",
                        "width": 1280,
                        "height": 720,
                        "avg_frame_rate": "30/1",
                    },
                ),
                patch("candidate_mining.detected.cut_clip", side_effect=fake_cut),
            ):
                result = mine_person_detection_video(
                    video_path=video,
                    detection_entry={
                        "video_path": "data/raw/demo.mp4",
                        "person_timestamps_ms": [45_000, 46_000],
                        "hits": [
                            {"timestamp_ms": 45_000, "confidence": 0.7},
                            {"timestamp_ms": 46_000, "confidence": 0.8},
                        ],
                        "detector": "unit-detector",
                        "settings": {"sample_interval_ms": 1000},
                    },
                    output_dir=output_dir,
                    dataset_id="unit-detected",
                    random_seed=7,
                    merge_gap_ms=3_000,
                    padding_ms=5_000,
                    background_count=2,
                    background_duration_ms=10_000,
                    project_root=project_root,
                )

            manifest = load_json(output_dir / "candidate-manifest.json")
            errors = validate_candidate_manifest(
                manifest,
                file=result["manifest_path"],
                check_files=True,
                project_root=project_root,
            )
            self.assertEqual(errors, [])
            self.assertEqual(result["event_count"], 1)
            self.assertEqual(result["background_count"], 2)
            self.assertEqual(result["sample_count"], 3)
            self.assertTrue((output_dir / "inventory.json").exists())
            self.assertTrue((output_dir / "run-summary.json").exists())
            self.assertTrue((output_dir / "processing.log").exists())

            event = [sample for sample in manifest["samples"] if sample["clip_type"] == "event"][0]
            self.assertEqual(event["start_ms"], 40_000)
            self.assertEqual(event["end_ms"], 51_000)
            self.assertEqual(event["candidate_rule"], "person_detected_v1")
            self.assertEqual(event["metadata"]["selection_source"], "person_detector")
            self.assertEqual(event["metadata"]["detector_max_confidence"], 0.8)


if __name__ == "__main__":
    unittest.main()
