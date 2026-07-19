"""Unit tests for the 'most suspicious' 60s clip selection.

Only the pure decision functions are tested here (anchor choice + window math);
the ffmpeg cut and detector run are exercised end-to-end by hand, not in CI.
"""

from __future__ import annotations

import unittest

from candidate_mining.suspicious_clip import (
    choose_suspicious_anchor,
    suspicious_window,
)


class ChooseSuspiciousAnchorTest(unittest.TestCase):
    def test_single_episode_returns_first_hit(self) -> None:
        hits = [
            {"timestamp_ms": 10_000, "confidence": 0.4},
            {"timestamp_ms": 12_000, "confidence": 0.9},
            {"timestamp_ms": 14_000, "confidence": 0.5},
        ]
        # Episode's first appearance, not the peak-confidence frame.
        self.assertEqual(choose_suspicious_anchor(hits, merge_gap_ms=3_000), 10_000)

    def test_picks_first_hit_of_highest_confidence_episode(self) -> None:
        hits = [
            # Episode A: early, weak (maybe a false positive).
            {"timestamp_ms": 5_000, "confidence": 0.35},
            {"timestamp_ms": 6_000, "confidence": 0.40},
            # Episode B: later, strong -> this is the suspicious one.
            {"timestamp_ms": 60_000, "confidence": 0.55},
            {"timestamp_ms": 61_000, "confidence": 0.88},
        ]
        self.assertEqual(choose_suspicious_anchor(hits, merge_gap_ms=3_000), 60_000)

    def test_ties_break_to_earliest_episode(self) -> None:
        hits = [
            {"timestamp_ms": 5_000, "confidence": 0.8},
            {"timestamp_ms": 60_000, "confidence": 0.8},
        ]
        self.assertEqual(choose_suspicious_anchor(hits, merge_gap_ms=3_000), 5_000)

    def test_empty_hits_raises(self) -> None:
        with self.assertRaises(ValueError):
            choose_suspicious_anchor([], merge_gap_ms=3_000)


class SuspiciousWindowTest(unittest.TestCase):
    def test_centered_window_is_60s(self) -> None:
        window = suspicious_window(100_000, duration_ms=200_000, half_ms=30_000)
        self.assertEqual((window.start_ms, window.end_ms), (70_000, 130_000))
        self.assertEqual(window.duration_ms, 60_000)

    def test_near_start_shifts_right_to_keep_60s(self) -> None:
        window = suspicious_window(10_000, duration_ms=200_000, half_ms=30_000)
        self.assertEqual((window.start_ms, window.end_ms), (0, 60_000))
        self.assertEqual(window.duration_ms, 60_000)

    def test_near_end_shifts_left_to_keep_60s(self) -> None:
        window = suspicious_window(195_000, duration_ms=200_000, half_ms=30_000)
        self.assertEqual((window.start_ms, window.end_ms), (140_000, 200_000))
        self.assertEqual(window.duration_ms, 60_000)

    def test_short_video_returns_whole_video(self) -> None:
        window = suspicious_window(20_000, duration_ms=45_000, half_ms=30_000)
        self.assertEqual((window.start_ms, window.end_ms), (0, 45_000))


if __name__ == "__main__":
    unittest.main()
