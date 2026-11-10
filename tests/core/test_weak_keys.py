"""Unit tests for the weak-key tracker."""

from __future__ import annotations

from src.core.weak_keys import WeakKeyTracker


class TestWeakKeyTracker:
    def test_no_data_returns_empty(self) -> None:
        tracker = WeakKeyTracker()
        assert tracker.weak_keys() == []
        assert not tracker.has_data()

    def test_errors_are_ranked(self) -> None:
        tracker = WeakKeyTracker()
        for _ in range(10):
            tracker.record_attempt("e", "e")
        for _ in range(10):
            tracker.record_attempt("r", "t")
        weak = tracker.weak_keys(min_attempts=3)
        assert weak[0][0] == "r"
        assert weak[0][1] > 0.9

    def test_min_attempts_filters_noise(self) -> None:
        tracker = WeakKeyTracker()
        tracker.record_attempt("q", "w")
        assert tracker.weak_keys(min_attempts=3) == []

    def test_case_is_preserved(self) -> None:
        tracker = WeakKeyTracker()
        tracker.record_attempt("A", "a")
        tracker.record_attempt("A", "a")
        tracker.record_attempt("A", "a")
        weak = tracker.weak_keys(min_attempts=3)
        assert weak and weak[0][0] == "A"

    def test_record_session_aligns(self) -> None:
        tracker = WeakKeyTracker()
        tracker.record_session("abc", "axc")
        stats = tracker.key_stats("b")
        assert stats.attempts == 1
        assert stats.errors == 1

    def test_drill_falls_back_to_home_row(self) -> None:
        tracker = WeakKeyTracker()
        drill = tracker.generate_drill(length=40)
        assert len(drill) > 0

    def test_drill_features_weak_keys(self) -> None:
        tracker = WeakKeyTracker()
        for _ in range(20):
            tracker.record_attempt("ñ", "n")
        drill = tracker.generate_drill(length=60, top_n=3)
        assert "ñ" in drill

    def test_reset_clears_everything(self) -> None:
        tracker = WeakKeyTracker()
        tracker.record_attempt("a", "s")
        tracker.reset()
        assert tracker.weak_keys() == []
        assert not tracker.has_data()
