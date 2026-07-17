"""Person detector backends.

Two backends, because they are not interchangeable in practice:

- yolov4:        608x608 input, COCO. Finds people in perimeter CCTV, where a
                 person is a few dozen pixels tall. ~0.8s/frame on CPU.
- mobilenet-ssd: 300x300 input, VOC. ~25x faster and useless for that footage -
                 measured 0.000 confidence on real surveillance frames that
                 contain people, including with 3x3 tiling.

Both carry permissive licenses (darknet is public domain, MobileNet-SSD Caffe
is permissive). Ultralytics YOLO is deliberately not used: it is AGPL-3.0.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2

# MobileNet-SSD is trained on VOC, where person is class 15.
VOC_PERSON_CLASS_ID = 15
# YOLOv4 is trained on COCO, where person is class 0.
COCO_PERSON_CLASS_ID = 0


@dataclass
class PersonBox:
    """A person detection, coordinates normalized 0..1 so the box survives any
    later resize or proxy transcode the browser might apply."""

    x: float
    y: float
    w: float
    h: float
    confidence: float

    def to_dict(self) -> dict[str, float]:
        return {
            "x": round(self.x, 4),
            "y": round(self.y, 4),
            "w": round(self.w, 4),
            "h": round(self.h, 4),
            "confidence": round(self.confidence, 4),
        }


class PersonDetector(ABC):
    name: str

    @abstractmethod
    def detect_people(self, frame: Any, min_confidence: float) -> list[PersonBox]:
        """All person boxes in this frame, empty if none."""

    def best_person_confidence(self, frame: Any, min_confidence: float) -> float:
        """Highest person confidence in this frame, 0.0 if none."""
        boxes = self.detect_people(frame, min_confidence)
        return max((box.confidence for box in boxes), default=0.0)


class MobileNetSsdDetector(PersonDetector):
    name = "mobilenet-ssd"
    input_size = (300, 300)
    scale = 1.0 / 127.5
    mean = 127.5

    def __init__(self, model_dir: str | Path) -> None:
        directory = Path(model_dir)
        prototxt = directory / "MobileNetSSD_deploy.prototxt"
        caffemodel = directory / "MobileNetSSD_deploy.caffemodel"
        for required in (prototxt, caffemodel):
            if not required.exists():
                raise FileNotFoundError(
                    f"Model file missing: {required}. Run `make fetch-person-model` first."
                )
        self.net = cv2.dnn.readNetFromCaffe(str(prototxt), str(caffemodel))

    def detect_people(self, frame: Any, min_confidence: float) -> list[PersonBox]:
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, self.input_size), self.scale, self.input_size, self.mean
        )
        self.net.setInput(blob)
        detections = self.net.forward()

        boxes = []
        for index in range(detections.shape[2]):
            confidence = float(detections[0, 0, index, 2])
            class_id = int(detections[0, 0, index, 1])
            if class_id == VOC_PERSON_CLASS_ID and confidence >= min_confidence:
                # SSD already reports corners normalized 0..1.
                x1, y1, x2, y2 = (float(v) for v in detections[0, 0, index, 3:7])
                boxes.append(
                    PersonBox(
                        x=max(0.0, x1),
                        y=max(0.0, y1),
                        w=min(1.0, x2) - max(0.0, x1),
                        h=min(1.0, y2) - max(0.0, y1),
                        confidence=confidence,
                    )
                )
        return boxes


class YoloV4Detector(PersonDetector):
    name = "yolov4"

    def __init__(self, model_dir: str | Path, input_size: int = 608) -> None:
        directory = Path(model_dir)
        cfg = directory / "yolov4.cfg"
        weights = directory / "yolov4.weights"
        for required in (cfg, weights):
            if not required.exists():
                raise FileNotFoundError(
                    f"Model file missing: {required}. Run `make fetch-person-model` first."
                )
        self.net = cv2.dnn.readNetFromDarknet(str(cfg), str(weights))
        self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
        self.output_layers = self.net.getUnconnectedOutLayersNames()
        self.input_size = (input_size, input_size)

    def detect_people(self, frame: Any, min_confidence: float) -> list[PersonBox]:
        blob = cv2.dnn.blobFromImage(
            frame, 1 / 255.0, self.input_size, swapRB=True, crop=False
        )
        self.net.setInput(blob)
        outputs = self.net.forward(self.output_layers)

        boxes = []
        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = int(scores.argmax())
                confidence = float(scores[class_id])
                if class_id == COCO_PERSON_CLASS_ID and confidence >= min_confidence:
                    # YOLO gives center x,y and w,h, already normalized 0..1.
                    cx, cy, bw, bh = (float(v) for v in detection[0:4])
                    boxes.append(
                        PersonBox(
                            x=max(0.0, cx - bw / 2),
                            y=max(0.0, cy - bh / 2),
                            w=bw,
                            h=bh,
                            confidence=confidence,
                        )
                    )
        return boxes


def build_detector(model: str, models_root: str | Path) -> PersonDetector:
    root = Path(models_root)
    if model == "yolov4":
        return YoloV4Detector(root / "yolov4")
    if model == "mobilenet-ssd":
        return MobileNetSsdDetector(root / "mobilenet-ssd")
    raise ValueError(f"Unknown detector: {model}. Use 'yolov4' or 'mobilenet-ssd'.")
