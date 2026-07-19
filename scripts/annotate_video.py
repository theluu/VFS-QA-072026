"""Export a video with person boxes burned in, matching the reference format.

Samples at a fixed FPS, runs the detector on each sampled frame, and holds the
last boxes on the frames in between so the overlay looks continuous. Output is a
standalone MP4 a reviewer can just play.

Detection is a triage signal, not ground truth - see ADR-005. Boxes show what
the detector proposed; a human still confirms.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "candidate-mining" / "src"))

from candidate_mining.detectors import build_detector
from candidate_mining.tracking import IouTracker

REPO_ROOT = Path(__file__).resolve().parents[1]

# Distinct BGR colors so each tracked person keeps one color across the video.
TRACK_COLORS = [
    (0, 220, 60), (60, 160, 255), (230, 120, 40), (200, 60, 220),
    (40, 220, 220), (120, 90, 240), (90, 200, 120), (0, 140, 255),
]


def draw_tracks(frame, tracks, width: int, height: int) -> None:
    for track_id, (bx, by, bw, bh), confidence in tracks:
        color = TRACK_COLORS[track_id % len(TRACK_COLORS)]
        x, y = int(bx * width), int(by * height)
        w, h = int(bw * width), int(bh * height)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        label = f"person #{track_id} {confidence:.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        cv2.rectangle(frame, (x, y - th - 6), (x + tw + 4, y), color, -1)
        cv2.putText(
            frame, label, (x + 2, y - 4),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (10, 20, 10), 1, cv2.LINE_AA,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Source video path.")
    parser.add_argument("--output", default="", help="Annotated MP4 path.")
    parser.add_argument("--models-root", default="models")
    parser.add_argument(
        "--model", default="yolov8", choices=["yolov8", "yolov4", "mobilenet-ssd"]
    )
    parser.add_argument("--sample-fps", type=float, default=5.0, help="Detections per second.")
    parser.add_argument("--min-confidence", type=float, default=0.3)
    args = parser.parse_args(argv)

    source = REPO_ROOT / args.input if not Path(args.input).is_absolute() else Path(args.input)
    if not source.is_file():
        print(f"Not a file: {args.input}", file=sys.stderr)
        return 1

    output = (
        Path(args.output)
        if args.output
        else REPO_ROOT / "outputs" / "annotated" / f"{source.stem}_bbox.mp4"
    )
    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        detector = build_detector(args.model, REPO_ROOT / args.models_root)
    except Exception as exc:
        print(f"Cannot load detector: {exc}", file=sys.stderr)
        return 1

    capture = cv2.VideoCapture(str(source))
    if not capture.isOpened():
        print(f"Cannot open video: {source}", file=sys.stderr)
        return 1

    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    detect_every = max(1, round(fps / args.sample_fps))

    # Pipe raw BGR frames into ffmpeg for H.264. cv2.VideoWriter is unreliable in
    # opencv-headless (no bundled muxer); ffmpeg on stdin always works and gives
    # a browser-playable file in one pass.
    ffmpeg = subprocess.Popen(
        [
            "ffmpeg", "-v", "error", "-y",
            "-f", "rawvideo", "-pix_fmt", "bgr24",
            "-s", f"{width}x{height}", "-r", f"{fps}",
            "-i", "-",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(output),
        ],
        stdin=subprocess.PIPE,
    )

    tracker = IouTracker(iou_threshold=0.3, max_age=detect_every * 2, min_hits=2)
    frame_index = 0
    held_tracks: list = []
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if frame_index % detect_every == 0:
                found = detector.detect_people(frame, args.min_confidence)
                boxes = [(b.x, b.y, b.w, b.h) for b in found]
                confs = [b.confidence for b in found]
                held_tracks = tracker.update(boxes, confs)
            draw_tracks(frame, held_tracks, width, height)
            ffmpeg.stdin.write(frame.tobytes())
            frame_index += 1
            if total and frame_index % 120 == 0:
                print(f"  {frame_index}/{total} frames", flush=True)
    finally:
        capture.release()
        ffmpeg.stdin.close()
        ffmpeg.wait()

    if ffmpeg.returncode != 0:
        print(f"ffmpeg failed with code {ffmpeg.returncode}", file=sys.stderr)
        return 1

    try:
        shown = output.resolve().relative_to(REPO_ROOT)
    except ValueError:
        shown = output
    print(
        f"\nWrote {shown}  "
        f"({frame_index} frames, {tracker.distinct_count()} nguoi rieng biet)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
