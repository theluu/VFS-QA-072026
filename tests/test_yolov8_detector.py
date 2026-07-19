"""Unit tests for the Ultralytics YOLOv8 person detector backend.

The real ultralytics/torch stack is faked so these run without weights or a GPU.
What is actually under test is our own code: the pixel-xyxy -> normalized
PersonBox conversion and the predict() arguments we forward.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np


class _FakeTensor:
    def __init__(self, data: list) -> None:
        self._data = data

    def tolist(self) -> list:
        return self._data


class _FakeBoxes:
    def __init__(self, xyxy: list, conf: list) -> None:
        self.xyxy = _FakeTensor(xyxy)
        self.conf = _FakeTensor(conf)


class _FakeResult:
    def __init__(self, boxes) -> None:
        self.boxes = boxes


def _fake_ultralytics(result_boxes, recorder: dict):
    """Return a stand-in `ultralytics` module whose YOLO(...).predict records its
    kwargs and returns a single result with the given boxes."""

    class _FakeYOLO:
        def __init__(self, weights: str) -> None:
            recorder["weights"] = weights

        def predict(self, frame, **kwargs):
            recorder["predict_kwargs"] = kwargs
            return [_FakeResult(result_boxes)]

    module = type(sys)("ultralytics")
    module.YOLO = _FakeYOLO
    return module


class YoloV8DetectorTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.model_dir = Path(self._tmp.name)
        (self.model_dir / "yolov8m.pt").write_bytes(b"fake weights")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _detect(self, frame, min_confidence, result_boxes):
        from candidate_mining.detectors import YoloV8Detector

        recorder: dict = {}
        fake = _fake_ultralytics(result_boxes, recorder)
        detector = YoloV8Detector(self.model_dir)
        with patch.dict(sys.modules, {"ultralytics": fake}):
            boxes = detector.detect_people(frame, min_confidence)
        return boxes, recorder

    def test_normalizes_pixel_boxes_to_frame_dimensions(self) -> None:
        # cv2 frames are (height, width, channels): 500 tall, 1000 wide.
        frame = np.zeros((500, 1000, 3), dtype=np.uint8)
        result = _FakeBoxes(xyxy=[[100.0, 50.0, 300.0, 450.0]], conf=[0.87])
        boxes, _ = self._detect(frame, 0.3, result)

        self.assertEqual(len(boxes), 1)
        box = boxes[0]
        self.assertAlmostEqual(box.x, 0.1, places=4)
        self.assertAlmostEqual(box.y, 0.1, places=4)
        self.assertAlmostEqual(box.w, 0.2, places=4)
        self.assertAlmostEqual(box.h, 0.8, places=4)
        self.assertAlmostEqual(box.confidence, 0.87, places=4)

    def test_forwards_person_class_and_confidence_threshold(self) -> None:
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        result = _FakeBoxes(xyxy=[], conf=[])
        _, recorder = self._detect(frame, 0.42, result)

        kwargs = recorder["predict_kwargs"]
        self.assertEqual(kwargs["classes"], [0])
        self.assertAlmostEqual(kwargs["conf"], 0.42)
        # imgsz must be large: VIRAT people vanish at the ultralytics default 640.
        self.assertEqual(kwargs["imgsz"], 1920)

    def test_returns_empty_when_no_boxes(self) -> None:
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        boxes, _ = self._detect(frame, 0.3, None)
        self.assertEqual(boxes, [])

    def test_missing_weights_raises_file_not_found(self) -> None:
        from candidate_mining.detectors import YoloV8Detector

        with tempfile.TemporaryDirectory() as empty_dir:
            with self.assertRaises(FileNotFoundError):
                YoloV8Detector(Path(empty_dir))


class BuildDetectorTest(unittest.TestCase):
    def test_build_detector_returns_yolov8_backend(self) -> None:
        from candidate_mining.detectors import YoloV8Detector, build_detector

        with tempfile.TemporaryDirectory() as models_root:
            weights_dir = Path(models_root) / "yolov8"
            weights_dir.mkdir()
            (weights_dir / "yolov8m.pt").write_bytes(b"fake weights")
            detector = build_detector("yolov8", models_root)
            self.assertIsInstance(detector, YoloV8Detector)


if __name__ == "__main__":
    unittest.main()
