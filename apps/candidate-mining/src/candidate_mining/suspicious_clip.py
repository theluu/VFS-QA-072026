"""Cut the single most-suspicious 60-second clip from a video.

After the person detector runs, this picks the moment a person appears in the
strongest detection episode and cuts a 1-minute clip around it: 30s before the
person appears and 30s after. The clip is a review artifact under outputs/ - a
triage aid, not ground truth (see ADR-005).

Two decisions are isolated as pure functions so they are testable without a
video or the detector:
- choose_suspicious_anchor: which timestamp to center on.
- suspicious_window: the [start, end] the anchor maps to, kept at 60s and inside
  the source video.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .core import TimeWindow

DEFAULT_HALF_MS = 30_000  # 30s each side -> a 60s clip.
DEFAULT_MERGE_GAP_MS = 3_000  # hits within 3s are the same appearance episode.


def choose_suspicious_anchor(
    hits: list[dict[str, Any]], *, merge_gap_ms: int = DEFAULT_MERGE_GAP_MS
) -> int:
    """Return the timestamp (ms) a person first appears in the most suspicious
    episode - the episode holding the highest-confidence detection.

    Grouping hits into episodes (gap > merge_gap_ms starts a new one) means a
    brief early false positive does not outweigh a later, clearly-a-person
    stretch: we rank episodes by their peak confidence, then anchor on when the
    person shows up in the winning episode.
    """
    if merge_gap_ms < 0:
        raise ValueError("merge_gap_ms must be >= 0")
    if not hits:
        raise ValueError("No person detections to cut a suspicious clip from")

    ordered = sorted(hits, key=lambda hit: int(hit["timestamp_ms"]))

    episodes: list[list[dict[str, Any]]] = [[ordered[0]]]
    for hit in ordered[1:]:
        previous = int(episodes[-1][-1]["timestamp_ms"])
        if int(hit["timestamp_ms"]) - previous <= merge_gap_ms:
            episodes[-1].append(hit)
        else:
            episodes.append([hit])

    def episode_peak(episode: list[dict[str, Any]]) -> float:
        return max(float(hit.get("confidence", 0.0)) for hit in episode)

    def episode_start(episode: list[dict[str, Any]]) -> int:
        return int(episode[0]["timestamp_ms"])

    # Highest peak confidence wins; ties break to the earlier episode so the
    # result is deterministic.
    best = max(episodes, key=lambda ep: (episode_peak(ep), -episode_start(ep)))
    return episode_start(best)


def suspicious_window(
    anchor_ms: int, *, duration_ms: int, half_ms: int = DEFAULT_HALF_MS
) -> TimeWindow:
    """Map an anchor timestamp to a [start, end] window of length 2*half_ms.

    The window centers on the anchor, but slides to stay inside [0, duration_ms]
    so it keeps its full length near the video's start or end. A video shorter
    than the target length yields the whole video.
    """
    if half_ms <= 0:
        raise ValueError("half_ms must be > 0")
    if duration_ms <= 0:
        raise ValueError("duration_ms must be > 0")
    if not 0 <= anchor_ms <= duration_ms:
        raise ValueError("anchor_ms must be inside the source video duration")

    target = 2 * half_ms
    if duration_ms <= target:
        return TimeWindow(start_ms=0, end_ms=duration_ms)

    start = anchor_ms - half_ms
    end = anchor_ms + half_ms
    if start < 0:
        end -= start  # shift right by the overflow
        start = 0
    if end > duration_ms:
        start -= end - duration_ms  # shift left by the overflow
        end = duration_ms
    return TimeWindow(start_ms=start, end_ms=end)


def suspicious_clip_name(source: str | Path, window: TimeWindow) -> str:
    start_s = window.start_ms / 1000
    end_s = window.end_ms / 1000
    return f"{Path(source).stem}_suspect_{start_s:.0f}s-{end_s:.0f}s.mp4"


def cut_suspicious_clip(
    *,
    input_path: str | Path,
    output_dir: str | Path,
    models_root: str | Path,
    model: str = "yolov8",
    min_confidence: float = 0.3,
    min_hits: int = 2,
    sample_interval_ms: int = 1_000,
    merge_gap_ms: int = DEFAULT_MERGE_GAP_MS,
    half_ms: int = DEFAULT_HALF_MS,
) -> dict[str, Any]:
    """Detect people, then cut the most-suspicious 60s clip into output_dir.

    Raises ValueError if the video has fewer than min_hits person detections
    (nothing to cut). min_hits guards against a lone false positive.
    """
    # Imported here so this module's pure functions stay importable without cv2.
    from .person_detect import detect_persons_in_video, load_detector
    from .video import cut_clip, probe_video

    source = Path(input_path)
    if not source.is_file():
        raise FileNotFoundError(f"Not a file: {source}")

    duration_ms = probe_video(source)["duration_ms"]
    detector = load_detector(models_root, model)
    result = detect_persons_in_video(
        source,
        detector,
        sample_interval_ms=sample_interval_ms,
        min_confidence=min_confidence,
        min_hits=min_hits,
    )
    hits = [
        {"timestamp_ms": hit.timestamp_ms, "confidence": hit.confidence}
        for hit in result.hits
    ]
    if not result.has_person:
        raise ValueError(
            f"No person (>= {min_hits} hits) detected in {source.name}; nothing to cut"
        )

    anchor_ms = choose_suspicious_anchor(hits, merge_gap_ms=merge_gap_ms)
    window = suspicious_window(anchor_ms, duration_ms=duration_ms, half_ms=half_ms)

    output_dir = Path(output_dir)
    output_path = output_dir / suspicious_clip_name(source, window)
    cut_clip(source, output_path, window.start_ms, window.end_ms)

    peak_confidence = max(hit["confidence"] for hit in hits)
    return {
        "output_path": str(output_path),
        "source_video": source.name,
        "source_duration_ms": duration_ms,
        "person_appears_ms": anchor_ms,
        "clip_start_ms": window.start_ms,
        "clip_end_ms": window.end_ms,
        "clip_duration_ms": window.duration_ms,
        "detector": model,
        "max_confidence": round(peak_confidence, 4),
        "frames_with_person": result.frames_with_person,
        "frames_sampled": result.frames_sampled,
    }


def render_suspicious_bbox_clip(
    *,
    input_path: str | Path,
    output_dir: str | Path,
    models_root: str | Path,
    model: str = "yolov8",
    min_confidence: float = 0.3,
    min_hits: int = 2,
    sample_interval_ms: int = 2_000,
    bbox_sample_fps: float = 0.5,
    merge_gap_ms: int = DEFAULT_MERGE_GAP_MS,
    half_ms: int = DEFAULT_HALF_MS,
    on_progress: Any = None,
) -> dict[str, Any] | None:
    """Detect people, pick the suspicious 60s window, and write a clip of that
    window with the detector's boxes burned in (the on-video evidence).

    Returns None when the video has fewer than min_hits person detections
    (nothing to export - guards against a lone false positive); otherwise a
    metadata dict including the annotated clip path.

    Two passes on purpose: a whole-video scan (sample_interval_ms) locates the
    suspicious episode, then only that 60s window is re-run densely
    (bbox_sample_fps) to draw a smooth overlay. on_progress(done, total) is
    forwarded to the scan pass so a caller can show a bar.
    """
    from .bbox_video import render_person_bbox_video
    from .person_detect import detect_persons_in_video, load_detector
    from .video import cut_clip, probe_video

    source = Path(input_path)
    if not source.is_file():
        raise FileNotFoundError(f"Not a file: {source}")

    duration_ms = probe_video(source)["duration_ms"]
    detector = load_detector(models_root, model)
    result = detect_persons_in_video(
        source,
        detector,
        sample_interval_ms=sample_interval_ms,
        min_confidence=min_confidence,
        min_hits=min_hits,
        on_progress=on_progress,
    )
    hits = [
        {"timestamp_ms": hit.timestamp_ms, "confidence": hit.confidence}
        for hit in result.hits
    ]
    if not result.has_person:
        return None

    anchor_ms = choose_suspicious_anchor(hits, merge_gap_ms=merge_gap_ms)
    window = suspicious_window(anchor_ms, duration_ms=duration_ms, half_ms=half_ms)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = suspicious_clip_name(source, window).removesuffix(".mp4")
    final_path = output_dir / f"{stem}_bbox.mp4"
    raw_path = output_dir / f".raw_{stem}.mp4"

    try:
        # Cut the raw window first, then burn boxes onto just that window.
        cut_clip(source, raw_path, window.start_ms, window.end_ms)
        render_person_bbox_video(
            input_path=raw_path,
            output_path=final_path,
            models_root=models_root,
            model=model,
            sample_fps=bbox_sample_fps,
            min_confidence=min_confidence,
        )
    finally:
        raw_path.unlink(missing_ok=True)

    peak_confidence = max(hit["confidence"] for hit in hits)
    return {
        "output_path": str(final_path),
        "source_video": source.name,
        "source_duration_ms": duration_ms,
        "person_appears_ms": anchor_ms,
        "clip_start_ms": window.start_ms,
        "clip_end_ms": window.end_ms,
        "clip_duration_ms": window.duration_ms,
        "detector": model,
        "annotated": True,
        "max_confidence": round(peak_confidence, 4),
        "frames_with_person": result.frames_with_person,
        "frames_sampled": result.frames_sampled,
    }
