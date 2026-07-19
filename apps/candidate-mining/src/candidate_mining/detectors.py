"""Person detector backends.

Three backends, because they are not interchangeable in practice:

- yolov8:        Ultralytics YOLOv8, 1920px input, COCO. Best recall on small,
                 distant figures - this is the default and matches the reference
                 annotated sample. Needs torch, so it runs in a Python 3.11 venv
                 (torch has no build for this repo's newer Python).
- yolov4:        832x832 input, COCO, via OpenCV-DNN. No torch. Kept as a
                 permissive-license fallback for envs without the YOLOv8 stack.
- mobilenet-ssd: 300x300 input, VOC. ~25x faster and useless for that footage -
                 measured 0.000 confidence on real surveillance frames that
                 contain people, including with 3x3 tiling.

Licensing note: yolov4 (darknet, public domain) and MobileNet-SSD Caffe are
permissive. Ultralytics YOLOv8 is AGPL-3.0; it was previously avoided for that
reason, but the POC now accepts the AGPL trade-off to get the sample's detection
quality. See DECISIONS.md.
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
    # 832, not 608: on high-angle CCTV a distant person spans a few dozen pixels,
    # and 608 either misses them or scores them below threshold. Measured on VIRAT,
    # 832 lifts a distant figure from ~0.32 to ~0.9 and finds ones 608 dropped.
    NMS_IOU = 0.45

    def __init__(self, model_dir: str | Path, input_size: int = 832) -> None:
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

        # YOLO emits many overlapping boxes per object; collect then dedupe with
        # non-max suppression, or one person shows up as a stack of boxes.
        rects: list[list[float]] = []
        confidences: list[float] = []
        for output in outputs:
            for detection in output:
                scores = detection[5:]
                class_id = int(scores.argmax())
                confidence = float(scores[class_id])
                if class_id == COCO_PERSON_CLASS_ID and confidence >= min_confidence:
                    cx, cy, bw, bh = (float(v) for v in detection[0:4])
                    rects.append([cx - bw / 2, cy - bh / 2, bw, bh])
                    confidences.append(confidence)

        if not rects:
            return []

        keep = cv2.dnn.NMSBoxes(rects, confidences, min_confidence, self.NMS_IOU)
        indices = [int(i) for i in keep.flatten()] if len(keep) else []

        boxes = []
        for index in indices:
            x, y, bw, bh = rects[index]
            boxes.append(
                PersonBox(
                    x=max(0.0, x),
                    y=max(0.0, y),
                    w=bw,
                    h=bh,
                    confidence=confidences[index],
                )
            )
        return boxes


class YoloV8Detector(PersonDetector):
    name = "yolov8"
    # Mirrors the reference PersonYoloSettings: NMS is applied inside ultralytics,
    # so unlike the YOLOv4 path there is no separate NMSBoxes step here.
    IOU = 0.45

    def __init__(
        self, model_dir: str | Path, weight_name: str = "yolov8m.pt", input_size: int = 1920
    ) -> None:
        # 1920, not the ultralytics default 640: VIRAT people are a few dozen
        # pixels tall, and downscaling a 1280x720 frame to 640 shrinks them below
        # detectability. Measured on VIRAT, 640 finds 0 people, 1920 finds them at
        # ~0.4-0.7 confidence - matching the reference sample. Cost: ~2.5s/frame on
        # CPU (same trade-off the YOLOv4 backend makes with its 832 input).
        directory = Path(model_dir)
        self.weights = directory / weight_name
        if not self.weights.exists():
            raise FileNotFoundError(
                f"Model file missing: {self.weights}. Run `make fetch-person-model` first."
            )
        self.input_size = input_size
        self._model: Any | None = None

    def _load_model(self) -> Any:
        # ultralytics (and torch) are imported lazily so importing this module
        # never drags in the heavy stack; only building this backend does.
        if self._model is None:
            from ultralytics import YOLO

            self._model = YOLO(str(self.weights))
        return self._model

    def detect_people(self, frame: Any, min_confidence: float) -> list[PersonBox]:
        model = self._load_model()
        height, width = frame.shape[:2]
        results = model.predict(
            frame,
            classes=[COCO_PERSON_CLASS_ID],
            conf=min_confidence,
            iou=self.IOU,
            imgsz=self.input_size,
            device="cpu",
            verbose=False,
        )

        boxes: list[PersonBox] = []
        for result in results:
            if result.boxes is None:
                continue
            for xyxy, confidence in zip(
                result.boxes.xyxy.tolist(), result.boxes.conf.tolist()
            ):
                x1, y1, x2, y2 = (float(v) for v in xyxy)
                # ultralytics reports pixel corners; normalize 0..1 so the box
                # survives any later resize or proxy transcode, like the others.
                left = max(0.0, x1)
                top = max(0.0, y1)
                boxes.append(
                    PersonBox(
                        x=left / width,
                        y=top / height,
                        w=(min(float(width), x2) - left) / width,
                        h=(min(float(height), y2) - top) / height,
                        confidence=float(confidence),
                    )
                )
        return boxes


def build_detector(model: str, models_root: str | Path) -> PersonDetector:
    root = Path(models_root)
    if model == "yolov8":
        return YoloV8Detector(root / "yolov8")
    if model == "yolov4":
        return YoloV4Detector(root / "yolov4")
    if model == "mobilenet-ssd":
        return MobileNetSsdDetector(root / "mobilenet-ssd")
    raise ValueError(
        f"Unknown detector: {model}. Use 'yolov8', 'yolov4' or 'mobilenet-ssd'."
    )
