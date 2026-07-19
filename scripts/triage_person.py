"""Triage raw videos: which contain people, which get rejected.

Input:  a directory of videos, or data/raw/catalog.json
Output: outputs/reports/triage-report.json, plus (with --sort-dir) the videos
        split into co-nguoi/ and khong-co-nguoi/ folders you can just open.

Triage only. A rejected video is one no human needs to review for intrusion;
it is not a labeled sample, and this script never writes ground truth.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "candidate-mining" / "src"))

from candidate_mining.person_detect import (
    VideoPersonResult,
    detect_persons_in_video,
    load_detector,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".avi"}


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def collect_videos(input_arg: str) -> list[Path]:
    target = REPO_ROOT / input_arg if not Path(input_arg).is_absolute() else Path(input_arg)

    if target.is_file() and target.suffix == ".json":
        catalog = json.loads(target.read_text(encoding="utf-8"))
        return [REPO_ROOT / item["video_path"] for item in catalog["videos"]]
    if target.is_file():
        return [target]
    if target.is_dir():
        return sorted(p for p in target.iterdir() if p.suffix.lower() in VIDEO_SUFFIXES)
    raise FileNotFoundError(f"Input not found: {input_arg}")


def display_path(path: str | Path) -> str:
    """Repo-relative when possible; videos may legitimately live outside the repo."""
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def build_report(
    results: list[VideoPersonResult],
    settings: dict[str, Any],
    detector_name: str = "yolov4",
) -> dict[str, Any]:
    videos = []
    for result in results:
        payload = result.to_dict()
        payload["video_path"] = display_path(payload["video_path"])
        payload["decision"] = "keep" if result.has_person else "rejected"
        payload["reject_reason"] = None if result.has_person else "no_person_detected"
        videos.append(payload)

    kept = [v["video_path"] for v in videos if v["decision"] == "keep"]
    rejected = [v["video_path"] for v in videos if v["decision"] == "rejected"]

    return {
        "schema_version": "1.0.0",
        "generated_at": utc_now(),
        "detector": detector_name,
        "settings": settings,
        "summary": {
            "total": len(videos),
            "kept": len(kept),
            "rejected": len(rejected),
        },
        "videos": videos,
        "kept": kept,
        "rejected": rejected,
    }


HAS_PERSON_DIR = "co-nguoi"
NO_PERSON_DIR = "khong-co-nguoi"


def sort_into_folders(report: dict[str, Any], sort_dir: Path, copy: bool) -> None:
    """Put each video in a co-nguoi/ or khong-co-nguoi/ folder.

    Symlinks by default: the corpus is gigabytes and duplicating it to view the
    split is waste. --copy-files makes real copies for handing the folder over.
    """
    targets = {
        "keep": sort_dir / HAS_PERSON_DIR,
        "rejected": sort_dir / NO_PERSON_DIR,
    }
    for directory in targets.values():
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True)

    for video in report["videos"]:
        source = (REPO_ROOT / video["video_path"]).resolve()
        destination = targets[video["decision"]] / source.name
        if copy:
            shutil.copy2(source, destination)
        else:
            os.symlink(source, destination)

    kept = len(report["kept"])
    rejected = len(report["rejected"])
    mode = "copy" if copy else "symlink"
    print(f"\nSorted ({mode}) into {sort_dir.relative_to(REPO_ROOT)}/")
    print(f"  {HAS_PERSON_DIR}/      {kept} video")
    print(f"  {NO_PERSON_DIR}/  {rejected} video")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/raw/catalog.json", help="Video dir, file, or catalog.json")
    parser.add_argument("--output", default="outputs/reports/triage-report.json")
    parser.add_argument("--models-root", default="models")
    parser.add_argument(
        "--model", default="yolov8", choices=["yolov8", "yolov4", "mobilenet-ssd"]
    )
    parser.add_argument("--sample-interval-ms", type=int, default=1000)
    parser.add_argument("--min-confidence", type=float, default=0.5)
    parser.add_argument(
        "--min-hits",
        type=int,
        default=2,
        help="Frames with a person before the video is kept; guards against one false positive.",
    )
    parser.add_argument(
        "--sort-dir",
        default="",
        help=f"Split videos into {HAS_PERSON_DIR}/ and {NO_PERSON_DIR}/ under this directory.",
    )
    parser.add_argument(
        "--copy-files",
        action="store_true",
        help="Copy instead of symlink when sorting. Duplicates the data.",
    )
    args = parser.parse_args(argv)

    try:
        videos = collect_videos(args.input)
    except Exception as exc:
        print(f"Cannot read input: {exc}", file=sys.stderr)
        return 1
    if not videos:
        print(f"No videos found in {args.input}", file=sys.stderr)
        return 1

    try:
        net = load_detector(REPO_ROOT / args.models_root, args.model)
    except Exception as exc:
        print(f"Cannot load detector: {exc}", file=sys.stderr)
        return 1

    results: list[VideoPersonResult] = []
    failures = 0
    for video in videos:
        name = video.name
        try:
            result = detect_persons_in_video(
                video,
                net,
                sample_interval_ms=args.sample_interval_ms,
                min_confidence=args.min_confidence,
                min_hits=args.min_hits,
            )
        except Exception as exc:
            print(f"  FAILED {name}: {exc}", file=sys.stderr)
            failures += 1
            continue
        results.append(result)
        mark = "PERSON " if result.has_person else "reject "
        print(
            f"{mark} {name:26} conf={result.max_confidence:.2f} "
            f"hits={result.frames_with_person}/{result.frames_sampled}"
        )

    report = build_report(
        results,
        {
            "sample_interval_ms": args.sample_interval_ms,
            "min_confidence": args.min_confidence,
            "min_hits": args.min_hits,
        },
        detector_name=args.model,
    )
    output_path = REPO_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    summary = report["summary"]
    print(f"\n{summary['kept']} kept, {summary['rejected']} rejected, {failures} failed")
    print(f"Wrote {args.output}")

    if args.sort_dir:
        try:
            sort_into_folders(report, REPO_ROOT / args.sort_dir, args.copy_files)
        except Exception as exc:
            print(f"Cannot sort into folders: {exc}", file=sys.stderr)
            return 1

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
