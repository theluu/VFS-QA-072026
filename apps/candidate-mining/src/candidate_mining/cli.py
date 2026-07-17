from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from scripts.validation_core import validate_candidate_manifest, write_json

from . import __version__
from .core import (
    TimeWindow,
    build_sample,
    clamp_event_window,
    load_candidate_events,
    safe_relative_path,
    sample_background_windows,
    stable_source_video_id,
)
from .video import cut_clip, probe_video

PROJECT_ROOT = Path(__file__).resolve().parents[4]


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_log(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate candidate manifest and proxy clips.")
    parser.add_argument("--input", required=True, help="Input video path.")
    parser.add_argument("--events", required=True, help="Candidate events JSON path.")
    parser.add_argument("--output", required=True, help="Output run directory.")
    parser.add_argument("--dataset-id", default="local-dataset")
    parser.add_argument("--manifest-id", default="")
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--background-count", type=int, default=2)
    parser.add_argument("--background-duration-ms", type=int, default=15000)
    parser.add_argument("--padding-ms", type=int, default=30000)
    return parser


def run(args: argparse.Namespace) -> int:
    output_dir = Path(args.output)
    clips_dir = output_dir / "clips"
    output_dir.mkdir(parents=True, exist_ok=True)
    clips_dir.mkdir(parents=True, exist_ok=True)
    log_lines: list[str] = []

    video_path = Path(args.input)
    events = load_candidate_events(args.events)
    video = probe_video(video_path)
    source_video_path = safe_relative_path(video_path, PROJECT_ROOT)
    source_video_id = stable_source_video_id(
        source_video_path,
        video["duration_ms"],
        video["file_size"],
    )
    inventory = {
        "schema_version": "1.0.0",
        "generated_at": utc_now(),
        "source_video_id": source_video_id,
        "source_video_path": source_video_path,
        **{key: value for key, value in video.items() if key != "path"},
    }
    write_json(output_dir / "inventory.json", inventory)
    log_lines.append(f"Probed video {source_video_path} duration_ms={video['duration_ms']}")

    samples: list[dict] = []
    event_windows: list[TimeWindow] = []
    for event in events:
        window = clamp_event_window(
            event["candidate_start_ms"],
            event["candidate_end_ms"],
            video["duration_ms"],
            padding_ms=args.padding_ms,
        )
        event_windows.append(window)
        sample_id = f"{source_video_id}__{window.start_ms}__{window.end_ms}__{event['candidate_rule']}"
        clip_path = clips_dir / f"{sample_id}.mp4"
        cut_clip(video_path, clip_path, window.start_ms, window.end_ms)
        sample = build_sample(
            source_video_id=source_video_id,
            source_video_path=source_video_path,
            source_video_duration_ms=video["duration_ms"],
            clip_path=safe_relative_path(clip_path, PROJECT_ROOT),
            clip_type="event",
            candidate_rule=event["candidate_rule"],
            window=window,
            metadata={
                "candidate_start_ms": event["candidate_start_ms"],
                "candidate_end_ms": event["candidate_end_ms"],
                "selection_source": "event_input",
                **event.get("metadata", {}),
            },
        )
        samples.append(sample)
        log_lines.append(f"Wrote event clip {sample['clip_path']}")

    background_windows = sample_background_windows(
        video["duration_ms"],
        event_windows,
        count=args.background_count,
        window_ms=args.background_duration_ms,
        random_seed=args.random_seed,
    )
    for window in background_windows:
        candidate_rule = "background_v1"
        sample_id = f"{source_video_id}__{window.start_ms}__{window.end_ms}__{candidate_rule}"
        clip_path = clips_dir / f"{sample_id}.mp4"
        cut_clip(video_path, clip_path, window.start_ms, window.end_ms)
        sample = build_sample(
            source_video_id=source_video_id,
            source_video_path=source_video_path,
            source_video_duration_ms=video["duration_ms"],
            clip_path=safe_relative_path(clip_path, PROJECT_ROOT),
            clip_type="background",
            candidate_rule=candidate_rule,
            window=window,
            metadata={
                "selection_source": "random_background",
                "random_seed": args.random_seed,
            },
        )
        samples.append(sample)
        log_lines.append(f"Wrote background clip {sample['clip_path']}")

    manifest_id = args.manifest_id or f"manifest-{source_video_id}-{args.random_seed}"
    manifest = {
        "schema_version": "1.0.0",
        "dataset_id": args.dataset_id,
        "manifest_id": manifest_id,
        "generated_at": utc_now(),
        "generator_version": f"candidate-mining-poc-{__version__}",
        "random_seed": args.random_seed,
        "samples": samples,
    }
    errors = validate_candidate_manifest(manifest, file=str(output_dir / "candidate-manifest.json"))
    if errors:
        write_json(output_dir / "validation-report.json", {"errors": errors})
        write_log(output_dir / "processing.log", log_lines)
        for error in errors:
            print(f"{error['error_code']}: {error['message']}", file=sys.stderr)
        return 1

    write_json(output_dir / "candidate-manifest.json", manifest)
    summary = {
        "schema_version": "1.0.0",
        "generated_at": utc_now(),
        "source_video_id": source_video_id,
        "event_count": len(event_windows),
        "background_count": len(background_windows),
        "sample_count": len(samples),
        "manifest_path": safe_relative_path(output_dir / "candidate-manifest.json", PROJECT_ROOT),
    }
    write_json(output_dir / "run-summary.json", summary)
    write_log(output_dir / "processing.log", log_lines)
    print(f"Wrote {output_dir / 'candidate-manifest.json'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run(args)
    except Exception as exc:
        print(f"candidate-mining failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
