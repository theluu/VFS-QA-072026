"""Lightweight IoU tracker to give each person a stable ID across frames.

The reference annotated video assigns persistent track IDs (t6, t14) and holds a
box on a person even on frames where the single-shot detector flickers. This is
a minimal SORT-style tracker: greedy IoU matching, no Kalman filter, numpy-free.
It runs in the project's Python 3.14 venv, so nothing new has to be installed
and the AGPL YOLO stack is avoided.

IoU matching only works when frames are close enough that a person overlaps
itself between them - dense sampling (a few FPS). At sparse triage sampling
(one frame per second or slower) a walker moves too far to overlap and tracks
fragment; the annotate-video path samples densely, so that is where IDs matter.
"""

from __future__ import annotations

from dataclasses import dataclass, field

Box = tuple[float, float, float, float]  # (x, y, w, h)


def iou(a: Box, b: Box) -> float:
    ax1, ay1, aw, ah = a
    bx1, by1, bw, bh = b
    ax2, ay2 = ax1 + aw, ay1 + ah
    bx2, by2 = bx1 + bw, by1 + bh

    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    intersection = iw * ih
    if intersection <= 0:
        return 0.0
    union = aw * ah + bw * bh - intersection
    return intersection / union if union > 0 else 0.0


@dataclass
class Track:
    track_id: int
    box: Box
    confidence: float
    hits: int = 1
    age_since_seen: int = 0


class IouTracker:
    """Assigns stable IDs to per-frame person boxes.

    - iou_threshold: minimum overlap to treat a detection as the same person.
    - max_age: consecutive missed frames a track survives before being dropped;
      this is what holds a box across a flickering detection.
    - min_hits: times a track must be seen before it counts as a real person,
      which suppresses one-frame false positives.
    """

    def __init__(
        self, iou_threshold: float = 0.3, max_age: int = 5, min_hits: int = 2
    ) -> None:
        self.iou_threshold = iou_threshold
        self.max_age = max_age
        self.min_hits = min_hits
        self._tracks: list[Track] = []
        self._next_id = 1
        self._confirmed_ids: set[int] = set()

    def update(
        self, boxes: list[Box], confidences: list[float]
    ) -> list[tuple[int, Box, float]]:
        """Feed one frame's detections; return (track_id, box, confidence) for
        every active track, including held ones with no detection this frame."""
        unmatched_dets = set(range(len(boxes)))
        matched_track_indices: set[int] = set()

        pairs = [
            (iou(track.box, boxes[det]), t_idx, det)
            for t_idx, track in enumerate(self._tracks)
            for det in range(len(boxes))
        ]
        pairs = [p for p in pairs if p[0] >= self.iou_threshold]
        pairs.sort(reverse=True)

        for _score, t_idx, det in pairs:
            if t_idx in matched_track_indices or det not in unmatched_dets:
                continue
            track = self._tracks[t_idx]
            track.box = boxes[det]
            track.confidence = confidences[det]
            track.hits += 1
            track.age_since_seen = 0
            matched_track_indices.add(t_idx)
            unmatched_dets.discard(det)
            if track.hits >= self.min_hits:
                self._confirmed_ids.add(track.track_id)

        # Age tracks that got no detection this frame; drop the stale ones.
        for t_idx, track in enumerate(self._tracks):
            if t_idx not in matched_track_indices:
                track.age_since_seen += 1
        self._tracks = [t for t in self._tracks if t.age_since_seen <= self.max_age]

        # New tracks for leftover detections.
        for det in unmatched_dets:
            self._tracks.append(
                Track(track_id=self._next_id, box=boxes[det], confidence=confidences[det])
            )
            self._next_id += 1

        return [
            (t.track_id, t.box, t.confidence)
            for t in self._tracks
            if t.hits >= self.min_hits or t.age_since_seen == 0
        ]

    def distinct_count(self) -> int:
        """Total distinct people confirmed over the whole run."""
        return len(self._confirmed_ids)
