from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TimeWindow:
    start_ms: int
    end_ms: int

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms


def safe_relative_path(path: str | Path, project_root: Path) -> str:
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return f"external/{resolved.name}"


def stable_source_video_id(source_video_path: str, duration_ms: int, file_size: int) -> str:
    payload = f"{source_video_path}|{duration_ms}|{file_size}".encode("utf-8")
    return hashlib.sha1(payload).hexdigest()[:12]


def make_sample_id(
    source_video_id: str,
    start_ms: int,
    end_ms: int,
    candidate_rule_version: str,
) -> str:
    rule = candidate_rule_version.replace(" ", "_")
    return f"{source_video_id}__{start_ms}__{end_ms}__{rule}"


def clamp_event_window(
    candidate_start_ms: int,
    candidate_end_ms: int,
    source_video_duration_ms: int,
    *,
    padding_ms: int = 30000,
) -> TimeWindow:
    if candidate_start_ms < 0:
        raise ValueError("candidate_start_ms must be >= 0")
    if candidate_end_ms <= candidate_start_ms:
        raise ValueError("candidate_end_ms must be greater than candidate_start_ms")
    if candidate_start_ms >= source_video_duration_ms:
        raise ValueError("candidate_start_ms must be inside source video duration")
    start_ms = max(0, candidate_start_ms - padding_ms)
    end_ms = min(source_video_duration_ms, candidate_end_ms + padding_ms)
    if end_ms <= start_ms:
        raise ValueError("normalized event window is empty")
    return TimeWindow(start_ms=start_ms, end_ms=end_ms)


def windows_overlap(left: TimeWindow, right: TimeWindow) -> bool:
    return left.start_ms < right.end_ms and right.start_ms < left.end_ms


def sample_background_windows(
    source_video_duration_ms: int,
    exclusion_windows: list[TimeWindow],
    *,
    count: int,
    window_ms: int = 15000,
    random_seed: int = 42,
    max_attempts: int = 10000,
) -> list[TimeWindow]:
    if count <= 0:
        return []
    if window_ms <= 0:
        raise ValueError("window_ms must be > 0")
    if source_video_duration_ms < window_ms:
        return []

    rng = random.Random(random_seed)
    selected: list[TimeWindow] = []
    latest_start = source_video_duration_ms - window_ms
    attempts = 0
    while len(selected) < count and attempts < max_attempts:
        attempts += 1
        start_ms = rng.randint(0, latest_start)
        candidate = TimeWindow(start_ms=start_ms, end_ms=start_ms + window_ms)
        if any(windows_overlap(candidate, blocked) for blocked in exclusion_windows):
            continue
        if any(windows_overlap(candidate, existing) for existing in selected):
            continue
        selected.append(candidate)
    return sorted(selected, key=lambda item: item.start_ms)


def load_candidate_events(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    events = payload.get("events")
    if not isinstance(events, list):
        raise ValueError("events file must contain an events array")
    normalized = []
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            raise ValueError(f"events[{index}] must be an object")
        for field in ("candidate_start_ms", "candidate_end_ms"):
            if not isinstance(event.get(field), int):
                raise ValueError(f"events[{index}].{field} must be integer milliseconds")
        candidate_rule = str(event.get("candidate_rule") or "manual_candidate_v1")
        normalized.append(
            {
                "candidate_rule": candidate_rule,
                "candidate_start_ms": event["candidate_start_ms"],
                "candidate_end_ms": event["candidate_end_ms"],
                "metadata": event.get("metadata", {}),
            }
        )
    return normalized


def build_sample(
    *,
    source_video_id: str,
    source_video_path: str,
    source_video_duration_ms: int,
    clip_path: str,
    clip_type: str,
    candidate_rule: str,
    window: TimeWindow,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "sample_id": make_sample_id(
            source_video_id,
            window.start_ms,
            window.end_ms,
            candidate_rule,
        ),
        "source_video_id": source_video_id,
        "source_video_path": source_video_path,
        "source_video_duration_ms": source_video_duration_ms,
        "clip_path": clip_path,
        "clip_type": clip_type,
        "candidate_rule": candidate_rule,
        "start_ms": window.start_ms,
        "end_ms": window.end_ms,
        "duration_ms": window.duration_ms,
        "metadata": metadata,
    }
