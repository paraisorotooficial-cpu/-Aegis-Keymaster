"""Tests for latency tracking and keystroke-log ingestion in weak keys."""

from __future__ import annotations

from src.core.weak_keys import WeakKeyTracker


class TestIngestLog:
    def make_log(self) -> list[dict]:
        return [
            {"expected": "a", "typed": "a", "correct": True, "offset": 0.0, "is_backspace": False},
            {"expected": "b", "typed": "x", "correct": False, "offset": 1.0, "is_backspace": False},
            {"expected": "b", "typed": "\b", "correct": False, "offset": 1.2, "is_backspace": True},
            {"expected": "b", "typed": "b", "correct": True, "offset": 2.0, "is_backspace": False},
        ]

    def test_ingest_counts_attempts_and_errors(self) -> None:
        tracker = WeakKeyTracker()
        tracker.ingest_log(self.make_log())
        stats = tracker.all_stats()
        assert stats["a"].attempts == 1
        assert stats["b"].attempts == 2
        assert stats["b"].errors == 1
        assert tracker.weak_keys(min_attempts=1)[0][0] == "b"

    def test_ingest_measures_latency(self) -> None:
        tracker = WeakKeyTracker()
        tracker.ingest_log(self.make_log())
        stats = tracker.all_stats()
        assert stats["b"].latency_samples == 2
        assert stats["b"].avg_latency == 1.0

    def test_first_keystroke_has_no_latency(self) -> None:
        tracker = WeakKeyTracker()
        tracker.ingest_log(self.make_log())
        assert tracker.all_stats()["a"].latency_samples == 0

    def test_backspaces_are_skipped(self) -> None:
        tracker = WeakKeyTracker()
        tracker.ingest_log(self.make_log())
        stats = tracker.all_stats()
        assert sum(s.attempts for s in stats.values()) == 3

    def test_empty_log_is_safe(self) -> None:
        tracker = WeakKeyTracker()
        tracker.ingest_log([])
        assert not tracker.has_data()

    def test_malformed_entries_are_skipped(self) -> None:
        tracker = WeakKeyTracker()
        tracker.ingest_log([{"typed": "x"}, {"expected": "", "typed": "y"}, {}])
        assert not tracker.has_data()

    def test_feeds_from_typing_test_session(self) -> None:
        from src.core.typing_test import TypingTestSession

        clock = {"now": 100.0}

        def tick() -> float:
            return clock["now"]

        session = TypingTestSession("ab", 60, clock=tick)
        session.type_char("a")
        clock["now"] += 0.5
        session.type_char("b")
        tracker = WeakKeyTracker()
        tracker.ingest_log(session.keystroke_log())
        stats = tracker.all_stats()
        assert stats["a"].attempts == 1
        assert stats["b"].avg_latency == 0.5
