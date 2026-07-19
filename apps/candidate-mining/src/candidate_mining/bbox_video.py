from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import cv2

from scripts.validation_core import REPO_ROOT

from .detectors import build_detector
from .tracking import IouTracker
from .video import probe_video

TRACK_COLORS = [
    (0, 220, 60),
    (60, 160, 255),
    (230, 120, 40),
    (200, 60, 220),
    (40, 220, 220),
    (120, 90, 240),
    (90, 200, 120),
    (0, 140, 255),
]


def bbox_output_name(source: str | Path, duration_ms: int) -> str:
    duration_s = duration_ms / 1000
    return f"{Path(source).stem}_person_detected-0001_0.0s-{duration_s:.1f}s_bbox.mp4"


def draw_tracks(frame: Any, tracks: list[tuple[int, tuple[float, float, float, float], float]]) -> None:
    height, width = frame.shape[:2]
    for track_id, (bx, by, bw, bh), confidence in tracks:
        color = TRACK_COLORS[track_id % len(TRACK_COLORS)]
        x, y = int(bx * width), int(by * height)
        w, h = int(bw * width), int(bh * height)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        label = f"person #{track_id} {confidence:.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        cv2.rectangle(frame, (x, y - th - 6), (x + tw + 4, y), color, -1)
        cv2.putText(
            frame,
            label,
            (x + 2, y - 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (10, 20, 10),
            1,
            cv2.LINE_AA,
        )


def render_person_bbox_video(
    *,
    input_path: str | Path,
    output_path: str | Path | None = None,
    models_root: str | Path = REPO_ROOT / "models",
    model: str = "yolov8",
    sample_fps: float = 5.0,
    min_confidence: float = 0.3,
) -> dict[str, Any]:
    if sample_fps <= 0:
        raise ValueError("sample_fps must be > 0")
    if not 0 <= min_confidence <= 1:
        raise ValueError("min_confidence must be between 0 and 1")

    source = Path(input_path)
    if not source.is_file():
        raise FileNotFoundError(f"Not a file: {source}")

    probe = probe_video(source)
    output = Path(output_path) if output_path else REPO_ROOT / "outputs" / "annotated" / bbox_output_name(
        source, probe["duration_ms"]
    )
    output.parent.mkdir(parents=True, exist_ok=True)

    detector = build_detector(model, models_root)
    capture = cv2.VideoCapture(str(source))
    if not capture.isOpened():
        raise ValueError(f"Cannot open video: {source}")

    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    detect_every = max(1, round(fps / sample_fps))

    ffmpeg = subprocess.Popen(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "bgr24",
            "-s",
            f"{width}x{height}",
            "-r",
            f"{fps}",
            "-i",
            "-",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "24",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output),
        ],
        stdin=subprocess.PIPE,
    )
    if ffmpeg.stdin is None:
        raise RuntimeError("Cannot open ffmpeg stdin")

    tracker = IouTracker(iou_threshold=0.3, max_age=detect_every * 2, min_hits=2)
    frame_index = 0
    held_tracks: list[tuple[int, tuple[float, float, float, float], float]] = []
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if frame_index % detect_every == 0:
                found = detector.detect_people(frame, min_confidence)
                boxes = [(box.x, box.y, box.w, box.h) for box in found]
                confidences = [box.confidence for box in found]
                held_tracks = tracker.update(boxes, confidences)
            draw_tracks(frame, held_tracks)
            ffmpeg.stdin.write(frame.tobytes())
            frame_index += 1
    finally:
        capture.release()
        ffmpeg.stdin.close()
        ffmpeg.wait()

    if ffmpeg.returncode != 0:
        output.unlink(missing_ok=True)
        raise RuntimeError(f"ffmpeg failed with code {ffmpeg.returncode}")

    return {
        "output_path": output.relative_to(REPO_ROOT).as_posix(),
        "frame_count": frame_index,
        "source_frame_count": total,
        "duration_ms": probe["duration_ms"],
        "distinct_people": tracker.distinct_count(),
        "model": model,
        "sample_fps": sample_fps,
        "min_confidence": min_confidence,
    }
