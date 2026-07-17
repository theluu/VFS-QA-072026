"""Detect whether a video contains people, by sampling frames.

This is a triage signal only: it decides which videos a human should look at.
It never sets a label or a ground truth status - see ADR-005.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cv2

# MobileNet-SSD is trained on VOC; "person" is class index 15.
PERSON_CLASS_ID = 15
INPUT_SIZE = (300, 300)
MEAN_VALUE = 127.5
SCALE_FACTOR = 1.0 / 127.5


@dataclass
class PersonHit:
    timestamp_ms: int
    confidence: float


@dataclass
class VideoPersonResult:
    video_path: str
    has_person: bool
    max_confidence: float
    frames_sampled: int
    frames_with_person: int
    hits: list[PersonHit] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "video_path": self.video_path,
            "has_person": self.has_person,
            "max_confidence": round(self.max_confidence, 4),
            "frames_sampled": self.frames_sampled,
            "frames_with_person": self.frames_with_person,
            "person_timestamps_ms": [hit.timestamp_ms for hit in self.hits],
            "hits": [
                {"timestamp_ms": hit.timestamp_ms, "confidence": round(hit.confidence, 4)}
                for hit in self.hits
            ],
        }


def load_detector(model_dir: str | Path) -> cv2.dnn.Net:
    model_path = Path(model_dir)
    prototxt = model_path / "MobileNetSSD_deploy.prototxt"
    caffemodel = model_path / "MobileNetSSD_deploy.caffemodel"
    for required in (prototxt, caffemodel):
        if not required.exists():
            raise FileNotFoundError(
                f"Model file missing: {required}. Run `make fetch-person-model` first."
            )
    return cv2.dnn.readNetFromCaffe(str(prototxt), str(caffemodel))


def detect_persons_in_frame(net: cv2.dnn.Net, frame: Any, min_confidence: float) -> float:
    """Return the highest person confidence in this frame, 0.0 if none."""
    blob = cv2.dnn.blobFromImage(
        cv2.resize(frame, INPUT_SIZE),
        SCALE_FACTOR,
        INPUT_SIZE,
        MEAN_VALUE,
    )
    net.setInput(blob)
    detections = net.forward()

    best = 0.0
    for index in range(detections.shape[2]):
        confidence = float(detections[0, 0, index, 2])
        class_id = int(detections[0, 0, index, 1])
        if class_id == PERSON_CLASS_ID and confidence >= min_confidence:
            best = max(best, confidence)
    return best


def detect_persons_in_video(
    video_path: str | Path,
    net: cv2.dnn.Net,
    *,
    sample_interval_ms: int = 1000,
    min_confidence: float = 0.5,
    min_hits: int = 1,
) -> VideoPersonResult:
    """Sample one frame every sample_interval_ms and look for people.

    min_hits guards against a single false positive flagging a whole video.
    """
    path = Path(video_path)
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError(f"Cannot open video: {path}")

    try:
        fps = capture.get(cv2.CAP_PROP_FPS) or 0
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if fps <= 0 or frame_count <= 0:
            raise ValueError(f"Cannot read frame rate or frame count: {path}")

        duration_ms = int(frame_count / fps * 1000)
        hits: list[PersonHit] = []
        frames_sampled = 0
        max_confidence = 0.0

        for timestamp_ms in range(0, duration_ms, sample_interval_ms):
            capture.set(cv2.CAP_PROP_POS_MSEC, timestamp_ms)
            ok, frame = capture.read()
            if not ok or frame is None:
                continue
            frames_sampled += 1
            confidence = detect_persons_in_frame(net, frame, min_confidence)
            max_confidence = max(max_confidence, confidence)
            if confidence > 0:
                hits.append(PersonHit(timestamp_ms=timestamp_ms, confidence=confidence))

        return VideoPersonResult(
            video_path=str(path),
            has_person=len(hits) >= min_hits,
            max_confidence=max_confidence,
            frames_sampled=frames_sampled,
            frames_with_person=len(hits),
            hits=hits,
        )
    finally:
        capture.release()
