from __future__ import annotations

import unittest

from candidate_mining.core import (
    TimeWindow,
    clamp_event_window,
    make_sample_id,
    sample_background_windows,
    stable_source_video_id,
    windows_overlap,
)


class CandidateMiningCoreTest(unittest.TestCase):
    def test_clamp_event_window_uses_30_second_padding(self) -> None:
        window = clamp_event_window(45_000, 52_000, 120_000, padding_ms=30_000)
        self.assertEqual(window.start_ms, 15_000)
        self.assertEqual(window.end_ms, 82_000)
        self.assertEqual(window.duration_ms, 67_000)

    def test_clamp_event_window_does_not_go_negative(self) -> None:
        window = clamp_event_window(5_000, 8_000, 120_000, padding_ms=30_000)
        self.assertEqual(window.start_ms, 0)
        self.assertEqual(window.end_ms, 38_000)

    def test_sample_id_is_deterministic(self) -> None:
        source_id = stable_source_video_id("data/raw/sample.mp4", 120_000, 1024)
        self.assertEqual(source_id, stable_source_video_id("data/raw/sample.mp4", 120_000, 1024))
        self.assertEqual(
            make_sample_id(source_id, 15_000, 82_000, "intrusion_manual_v1"),
            f"{source_id}__15000__82000__intrusion_manual_v1",
        )

    def test_background_sampling_is_reproducible_and_excludes_events(self) -> None:
        exclusions = [TimeWindow(15_000, 82_000)]
        left = sample_background_windows(
            120_000,
            exclusions,
            count=2,
            window_ms=10_000,
            random_seed=7,
        )
        right = sample_background_windows(
            120_000,
            exclusions,
            count=2,
            window_ms=10_000,
            random_seed=7,
        )
        self.assertEqual(left, right)
        self.assertEqual(len(left), 2)
        for window in left:
            self.assertFalse(any(windows_overlap(window, blocked) for blocked in exclusions))


if __name__ == "__main__":
    unittest.main()
