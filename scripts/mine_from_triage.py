"""Cut candidate clips where the detector actually saw people.

mine_all.py cuts a window at a fixed 40%-60% of each video, which has nothing to
do with whether anyone is in frame - a reviewer opening those clips is looking at
an arbitrary slice. This reads triage-report.json and cuts clips around the
timestamps a person was detected, so the annotation tool shows candidates worth
reviewing.

The detector picks where to look. It does not label: candidate_rule records that
a person was detected, and every sample still arrives unreviewed.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "candidate-mining" / "src"))

from candidate_mining import __version__
from candidate_mining.core import (
    TimeWindow,
    build_sample,
    safe_relative_path,
    stable_source_video_id,
)
from candidate_mining.video import cut_clip, probe_video

from scripts.validation_core import validate_candidate_manifest, write_json

REPO_ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_RULE = "person_detected_v1"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def group_timestamps(
    timestamps: list[int],
    *,
    merge_gap_ms: int,
    padding_ms: int,
    duration_ms: int,
) -> list[TimeWindow]:
    """Merge nearby detections into one window, so a person walking through does
    not become a dozen one-second clips."""
    if not timestamps:
        return []

    ordered = sorted(timestamps)
    clusters: list[list[int]] = [[ordered[0]]]
    for stamp in ordered[1:]:
        if stamp - clusters[-1][-1] <= merge_gap_ms:
            clusters[-1].append(stamp)
        else:
            clusters.append([stamp])

    windows = []
    for cluster in clusters:
        start = max(0, cluster[0] - padding_ms)
        end = min(duration_ms, cluster[-1] + padding_ms)
        if end > start:
            windows.append(TimeWindow(start_ms=start, end_ms=end))
    return windows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--triage", default="outputs/reports/triage-report.json")
    parser.add_argument("--output-root", default="outputs/runs")
    parser.add_argument("--dataset-id", default="person-triage")
    parser.add_argument("--merge-gap-ms", type=int, default=3000)
    parser.add_argument("--padding-ms", type=int, default=2000)
    parser.add_argument("--max-clips-per-video", type=int, default=6)
    parser.add_argument("--random-seed", type=int, default=42)
    args = parser.parse_args(argv)

    triage_path = REPO_ROOT / args.triage
    if not triage_path.exists():
        print(f"Missing {args.triage}. Run `make triage-person` first.", file=sys.stderr)
        return 1

    report = json.loads(triage_path.read_text(encoding="utf-8"))
    kept = [v for v in report["videos"] if v["decision"] == "keep"]
    if not kept:
        print("Triage kept no videos: nothing to mine.", file=sys.stderr)
        return 1

    failures = 0
    run_ids: list[str] = []

    for entry in kept:
        video_path = REPO_ROOT / entry["video_path"]
        if not video_path.exists():
            print(f"  MISSING {entry['video_path']}", file=sys.stderr)
            failures += 1
            continue

        run_id = video_path.stem
        output_dir = REPO_ROOT / args.output_root / run_id
        clips_dir = output_dir / "clips"
        clips_dir.mkdir(parents=True, exist_ok=True)

        try:
            video = probe_video(video_path)
        except Exception as exc:
            print(f"  FAILED probe {run_id}: {exc}", file=sys.stderr)
            failures += 1
            continue

        windows = group_timestamps(
            entry["person_timestamps_ms"],
            merge_gap_ms=args.merge_gap_ms,
            padding_ms=args.padding_ms,
            duration_ms=video["duration_ms"],
        )[: args.max_clips_per_video]

        if not windows:
            print(f"  skip {run_id}: no person timestamps")
            continue

        source_video_path = safe_relative_path(video_path, REPO_ROOT)
        source_video_id = stable_source_video_id(
            source_video_path, video["duration_ms"], video["file_size"]
        )

        samples = []
        confidence_by_ts = {
            hit["timestamp_ms"]: hit["confidence"] for hit in entry.get("hits", [])
        }
        for window in windows:
            sample_id = f"{source_video_id}__{window.start_ms}__{window.end_ms}__{CANDIDATE_RULE}"
            clip_path = clips_dir / f"{sample_id}.mp4"
            try:
                cut_clip(video_path, clip_path, window.start_ms, window.end_ms)
            except Exception as exc:
                print(f"  FAILED clip {run_id}: {exc}", file=sys.stderr)
                failures += 1
                continue
            in_window = [
                conf
                for ts, conf in confidence_by_ts.items()
                if window.start_ms <= ts <= window.end_ms
            ]
            samples.append(
                build_sample(
                    source_video_id=source_video_id,
                    source_video_path=source_video_path,
                    source_video_duration_ms=video["duration_ms"],
                    clip_path=safe_relative_path(clip_path, REPO_ROOT),
                    clip_type="event",
                    candidate_rule=CANDIDATE_RULE,
                    window=window,
                    metadata={
                        "selection_source": "person_detector",
                        "detector": report.get("detector", "unknown"),
                        "detector_max_confidence": max(in_window) if in_window else None,
                        "detector_hits_in_window": len(in_window),
                    },
                )
            )

        if not samples:
            continue

        manifest = {
            "schema_version": "1.0.0",
            "dataset_id": args.dataset_id,
            "manifest_id": f"manifest-{source_video_id}-person",
            "generated_at": utc_now(),
            "generator_version": f"candidate-mining-poc-{__version__}",
            "random_seed": args.random_seed,
            "samples": samples,
        }
        errors = validate_candidate_manifest(manifest, file=str(output_dir))
        if errors:
            print(f"  FAILED validate {run_id}: {errors[0]['message']}", file=sys.stderr)
            failures += 1
            continue

        write_json(output_dir / "candidate-manifest.json", manifest)
        run_ids.append(run_id)
        print(f"{run_id:26} {len(samples)} clip(s) quanh nguoi duoc detect")

    print(f"\n{len(run_ids)} run(s) ok, {failures} failed")
    for run_id in run_ids:
        print(f"  outputs/runs/{run_id}/candidate-manifest.json")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
