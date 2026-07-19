"""Cut the most-suspicious 60-second clip from a video.

Runs the person detector over the video, finds the strongest appearance episode,
and cuts a 1-minute clip centered on when the person appears (30s before, 30s
after), saved under outputs/suspicious/. The clip is a review artifact, not
ground truth - see ADR-005.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "candidate-mining" / "src"))

from candidate_mining.suspicious_clip import cut_suspicious_clip

REPO_ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Source video path.")
    parser.add_argument(
        "--output-dir",
        default="outputs/suspicious",
        help="Folder for the cut clip (default: outputs/suspicious).",
    )
    parser.add_argument("--models-root", default="models")
    parser.add_argument(
        "--model", default="yolov8", choices=["yolov8", "yolov4", "mobilenet-ssd"]
    )
    parser.add_argument("--min-confidence", type=float, default=0.3)
    parser.add_argument(
        "--min-hits",
        type=int,
        default=2,
        help="Min person detections to treat a video as having a person (default: 2).",
    )
    parser.add_argument(
        "--sample-interval-ms",
        type=int,
        default=1_000,
        help="How often to sample a frame for detection (default: 1000ms).",
    )
    args = parser.parse_args(argv)

    source = REPO_ROOT / args.input if not Path(args.input).is_absolute() else Path(args.input)
    if not source.is_file():
        print(f"Not a file: {args.input}", file=sys.stderr)
        return 1

    output_dir = (
        Path(args.output_dir)
        if Path(args.output_dir).is_absolute()
        else REPO_ROOT / args.output_dir
    )

    try:
        result = cut_suspicious_clip(
            input_path=source,
            output_dir=output_dir,
            models_root=REPO_ROOT / args.models_root,
            model=args.model,
            min_confidence=args.min_confidence,
            min_hits=args.min_hits,
            sample_interval_ms=args.sample_interval_ms,
        )
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Cannot cut suspicious clip: {exc}", file=sys.stderr)
        return 1

    written = Path(result["output_path"])
    try:
        shown = written.resolve().relative_to(REPO_ROOT)
    except ValueError:
        shown = written
    appears_s = result["person_appears_ms"] / 1000
    start_s = result["clip_start_ms"] / 1000
    end_s = result["clip_end_ms"] / 1000
    print(
        f"Nguoi xuat hien luc {appears_s:.1f}s (conf max {result['max_confidence']:.2f}).\n"
        f"Wrote {shown}  (clip {start_s:.1f}s-{end_s:.1f}s, "
        f"{result['clip_duration_ms'] / 1000:.0f}s)"
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
