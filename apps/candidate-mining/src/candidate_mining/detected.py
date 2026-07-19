from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.validation_core import REPO_ROOT, validate_candidate_manifest, write_json

from . import __version__
from .core import (
    TimeWindow,
    build_sample,
    make_sample_id,
    safe_relative_path,
    sample_background_windows,
    stable_source_video_id,
)
from .video import cut_clip, probe_video

CANDIDATE_RULE = "person_detected_v1"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_log(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def safe_run_id(video_path: str | Path) -> str:
    stem = Path(video_path).stem.lower()
    slug = re.sub(r"[^a-z0-9_.-]+", "-", stem).strip("-")
    return slug or "person-detected"


def merge_time_windows(windows: list[TimeWindow]) -> list[TimeWindow]:
    if not windows:
        return []
    ordered = sorted(windows, key=lambda item: (item.start_ms, item.end_ms))
    merged = [ordered[0]]
    for window in ordered[1:]:
        current = merged[-1]
        if window.start_ms <= current.end_ms:
            merged[-1] = TimeWindow(
                start_ms=current.start_ms,
                end_ms=max(current.end_ms, window.end_ms),
            )
        else:
            merged.append(window)
    return merged


def detection_windows_from_timestamps(
    timestamps_ms: list[int],
    *,
    merge_gap_ms: int,
    padding_ms: int,
    duration_ms: int,
) -> list[TimeWindow]:
    """Turn sparse detector hits into non-overlapping candidate windows."""
    if merge_gap_ms < 0:
        raise ValueError("merge_gap_ms must be >= 0")
    if padding_ms < 0:
        raise ValueError("padding_ms must be >= 0")
    if duration_ms <= 0:
        raise ValueError("duration_ms must be > 0")
    if not timestamps_ms:
        return []

    ordered = []
    for timestamp in timestamps_ms:
        if not isinstance(timestamp, int):
            raise ValueError("detector timestamps must be integer milliseconds")
        if timestamp < 0 or timestamp > duration_ms:
            raise ValueError("detector timestamp must be inside source video duration")
        ordered.append(timestamp)
    ordered.sort()

    clusters: list[list[int]] = [[ordered[0]]]
    for timestamp in ordered[1:]:
        if timestamp - clusters[-1][-1] <= merge_gap_ms:
            clusters[-1].append(timestamp)
        else:
            clusters.append([timestamp])

    windows = []
    for cluster in clusters:
        start_ms = max(0, cluster[0] - padding_ms)
        end_ms = min(duration_ms, cluster[-1] + padding_ms)
        if end_ms <= start_ms:
            end_ms = min(duration_ms, start_ms + 1)
        if end_ms > start_ms:
            windows.append(TimeWindow(start_ms=start_ms, end_ms=end_ms))
    return merge_time_windows(windows)


def _timestamps_for_entry(detection_entry: dict[str, Any]) -> list[int]:
    explicit = detection_entry.get("person_timestamps_ms")
    if isinstance(explicit, list):
        return explicit
    hits = detection_entry.get("hits")
    if isinstance(hits, list):
        return [hit["timestamp_ms"] for hit in hits if isinstance(hit, dict)]
    return []


def _hits_in_window(detection_entry: dict[str, Any], window: TimeWindow) -> list[dict[str, Any]]:
    hits = detection_entry.get("hits")
    if not isinstance(hits, list):
        return []
    selected = []
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        timestamp_ms = hit.get("timestamp_ms")
        if isinstance(timestamp_ms, int) and window.start_ms <= timestamp_ms <= window.end_ms:
            selected.append(hit)
    return selected


def _metadata_for_window(
    detection_entry: dict[str, Any],
    window: TimeWindow,
    *,
    detector: str,
    detector_settings: dict[str, Any],
) -> dict[str, Any]:
    hits = _hits_in_window(detection_entry, window)
    timestamps = [hit["timestamp_ms"] for hit in hits if isinstance(hit.get("timestamp_ms"), int)]
    confidences = [
        float(hit["confidence"]) for hit in hits if isinstance(hit.get("confidence"), (int, float))
    ]
    return {
        "candidate_start_ms": min(timestamps) if timestamps else window.start_ms,
        "candidate_end_ms": max(timestamps) if timestamps else window.end_ms,
        "selection_source": "person_detector",
        "detector": detector,
        "detector_settings": detector_settings,
        "detector_first_seen_ms": min(timestamps) if timestamps else None,
        "detector_last_seen_ms": max(timestamps) if timestamps else None,
        "detector_hits_in_window": len(hits),
        "detector_max_confidence": max(confidences) if confidences else None,
        "detector_timestamps_ms": timestamps,
    }


def mine_person_detection_video(
    *,
    video_path: str | Path,
    detection_entry: dict[str, Any],
    output_dir: str | Path,
    dataset_id: str = "person-detected",
    random_seed: int = 42,
    merge_gap_ms: int = 3000,
    padding_ms: int = 30000,
    max_clips_per_video: int = 6,
    background_count: int = 2,
    background_duration_ms: int = 15000,
    project_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    if max_clips_per_video <= 0:
        raise ValueError("max_clips_per_video must be > 0")
    if background_count < 0:
        raise ValueError("background_count must be >= 0")

    video_path = Path(video_path)
    output_dir = Path(output_dir)
    clips_dir = output_dir / "clips"
    output_dir.mkdir(parents=True, exist_ok=True)
    clips_dir.mkdir(parents=True, exist_ok=True)
    log_lines: list[str] = []

    video = probe_video(video_path)
    source_video_path = safe_relative_path(video_path, project_root)
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

    timestamps_ms = _timestamps_for_entry(detection_entry)
    event_windows = detection_windows_from_timestamps(
        timestamps_ms,
        merge_gap_ms=merge_gap_ms,
        padding_ms=padding_ms,
        duration_ms=video["duration_ms"],
    )[:max_clips_per_video]
    if not event_windows:
        raise ValueError("No person detector timestamps to mine")

    detector = str(detection_entry.get("detector") or "unknown")
    detector_settings = detection_entry.get("settings")
    if not isinstance(detector_settings, dict):
        detector_settings = {}

    samples: list[dict[str, Any]] = []
    for window in event_windows:
        sample_id = make_sample_id(source_video_id, window.start_ms, window.end_ms, CANDIDATE_RULE)
        clip_path = clips_dir / f"{sample_id}.mp4"
        cut_clip(video_path, clip_path, window.start_ms, window.end_ms)
        sample = build_sample(
            source_video_id=source_video_id,
            source_video_path=source_video_path,
            source_video_duration_ms=video["duration_ms"],
            clip_path=safe_relative_path(clip_path, project_root),
            clip_type="event",
            candidate_rule=CANDIDATE_RULE,
            window=window,
            metadata=_metadata_for_window(
                detection_entry,
                window,
                detector=detector,
                detector_settings=detector_settings,
            ),
        )
        samples.append(sample)
        log_lines.append(f"Wrote detector event clip {sample['clip_path']}")

    background_windows = sample_background_windows(
        video["duration_ms"],
        event_windows,
        count=background_count,
        window_ms=background_duration_ms,
        random_seed=random_seed,
    )
    for window in background_windows:
        candidate_rule = "background_v1"
        sample_id = make_sample_id(source_video_id, window.start_ms, window.end_ms, candidate_rule)
        clip_path = clips_dir / f"{sample_id}.mp4"
        cut_clip(video_path, clip_path, window.start_ms, window.end_ms)
        sample = build_sample(
            source_video_id=source_video_id,
            source_video_path=source_video_path,
            source_video_duration_ms=video["duration_ms"],
            clip_path=safe_relative_path(clip_path, project_root),
            clip_type="background",
            candidate_rule=candidate_rule,
            window=window,
            metadata={
                "selection_source": "random_background",
                "random_seed": random_seed,
            },
        )
        samples.append(sample)
        log_lines.append(f"Wrote background clip {sample['clip_path']}")

    manifest_path = output_dir / "candidate-manifest.json"
    manifest = {
        "schema_version": "1.0.0",
        "dataset_id": dataset_id,
        "manifest_id": f"manifest-{source_video_id}-person-{random_seed}",
        "generated_at": utc_now(),
        "generator_version": f"candidate-mining-poc-{__version__}",
        "random_seed": random_seed,
        "samples": samples,
    }
    errors = validate_candidate_manifest(
        manifest,
        file=str(manifest_path),
        check_files=True,
        project_root=project_root,
    )
    if errors:
        write_json(output_dir / "validation-report.json", {"errors": errors})
        write_log(output_dir / "processing.log", log_lines)
        raise ValueError(f"Manifest validation failed: {errors[0]['message']}")

    write_json(manifest_path, manifest)
    summary = {
        "schema_version": "1.0.0",
        "generated_at": utc_now(),
        "source_video_id": source_video_id,
        "event_count": len(event_windows),
        "background_count": len(background_windows),
        "sample_count": len(samples),
        "manifest_path": safe_relative_path(manifest_path, project_root),
    }
    write_json(output_dir / "run-summary.json", summary)
    write_log(output_dir / "processing.log", log_lines)
    return {
        "source_video_id": source_video_id,
        "video_path": source_video_path,
        "run_dir": safe_relative_path(output_dir, project_root),
        "inventory_path": safe_relative_path(output_dir / "inventory.json", project_root),
        "manifest_path": safe_relative_path(manifest_path, project_root),
        "summary_path": safe_relative_path(output_dir / "run-summary.json", project_root),
        "log_path": safe_relative_path(output_dir / "processing.log", project_root),
        "event_count": len(event_windows),
        "background_count": len(background_windows),
        "sample_count": len(samples),
    }
