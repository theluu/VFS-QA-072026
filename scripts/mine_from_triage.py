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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "candidate-mining" / "src"))

from candidate_mining.core import TimeWindow
from candidate_mining.detected import (
    detection_windows_from_timestamps,
    mine_person_detection_video,
    safe_run_id,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def group_timestamps(
    timestamps: list[int],
    *,
    merge_gap_ms: int,
    padding_ms: int,
    duration_ms: int,
) -> list[TimeWindow]:
    """Merge nearby detections into one window, so a person walking through does
    not become a dozen one-second clips."""
    return detection_windows_from_timestamps(
        timestamps,
        merge_gap_ms=merge_gap_ms,
        padding_ms=padding_ms,
        duration_ms=duration_ms,
    )


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

        run_id = safe_run_id(video_path)
        output_dir = REPO_ROOT / args.output_root / run_id
        try:
            result = mine_person_detection_video(
                video_path=video_path,
                detection_entry={
                    **entry,
                    "detector": report.get("detector", "unknown"),
                    "settings": report.get("settings", {}),
                },
                output_dir=output_dir,
                dataset_id=args.dataset_id,
                merge_gap_ms=args.merge_gap_ms,
                padding_ms=args.padding_ms,
                max_clips_per_video=args.max_clips_per_video,
                random_seed=args.random_seed,
                project_root=REPO_ROOT,
            )
        except Exception as exc:
            print(f"  FAILED mine {run_id}: {exc}", file=sys.stderr)
            failures += 1
            continue

        run_ids.append(run_id)
        print(
            f"{run_id:26} {result['event_count']} event clip(s), "
            f"{result['background_count']} background clip(s)"
        )

    print(f"\n{len(run_ids)} run(s) ok, {failures} failed")
    for run_id in run_ids:
        print(f"  outputs/runs/{run_id}/candidate-manifest.json")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
