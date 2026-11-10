"""Unit tests for the timed typing test core (brief §7.2)."""

from __future__ import annotations

import pytest
from src.core.typing_test import (
    ALLOWED_DURATIONS,
    INTERVAL_SECONDS,
    InvalidDurationError,
    TypingTestSession,
)


class FakeClock:
    """Deterministic clock advanced explicitly."""

    def __init__(self, start: float = 100.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def make_session(
    text: str = "hola mundo desde aegis", duration: int = 60
) -> tuple[TypingTestSession, FakeClock]:
    clock = FakeClock()
    return TypingTestSession(text, duration, clock=clock), clock


class TestSessionBasics:
    def test_invalid_duration_rejected(self) -> None:
        for bad in (0, 30, 120, -60):
            with pytest.raises(InvalidDurationError):
                TypingTestSession("texto", bad)

    @pytest.mark.parametrize("duration", ALLOWED_DURATIONS)
    def test_allowed_durations(self, duration: int) -> None:
        session = TypingTestSession("texto", duration)
        assert session.duration_seconds == duration

    def test_timer_starts_on_first_keystroke(self) -> None:
        session, clock = make_session()
        assert session.elapsed == 0.0
        session.type_char("h")
        assert session.elapsed == 0.0
        clock.advance(3.0)
        session.tick()
        assert session.elapsed == 3.0

    def test_tick_before_start_is_noop(self) -> None:
        session, clock = make_session()
        clock.advance(10)
        assert session.tick() is False
        assert session.elapsed == 0.0

    def test_finishes_when_time_runs_out(self) -> None:
        session, clock = make_session(duration=60)
        session.type_char("h")
        clock.advance(60.0)
        assert session.tick() is True
        assert session.finished

    def test_cursor_advances_on_error(self) -> None:
        session, _ = make_session("abc")
        session.type_char("x")
        assert session.position == 1
        assert session.states[0] == "incorrect"

    def test_backspace_restores_state(self) -> None:
        session, _ = make_session("abc")
        session.type_char("x")
        assert session.backspace() is True
        assert session.position == 0
        assert session.states[0] == "pending"
        assert session.backspace() is False

    def test_no_input_after_finish(self) -> None:
        session, clock = make_session(duration=60)
        session.type_char("h")
        clock.advance(60.0)
        session.tick()
        session.type_char("o")
        assert session.position == 1

    def test_extend_appends_text(self) -> None:
        session, _ = make_session("abc")
        session.extend("def")
        for char in "abcdef":
            session.type_char(char)
        assert session.position == 6


class TestMetrics:
    def test_wpm_definitions(self) -> None:
        session, clock = make_session("aaaaa bbbbb", duration=60)
        for char in "aaaaa":
            session.type_char(char)
        clock.advance(60.0)
        session.tick()
        result = session.result()
        assert result.elapsed_seconds == pytest.approx(60.0)
        assert result.correct_keystrokes == 5
        assert result.net_wpm == pytest.approx(1.0)
        assert result.gross_wpm == pytest.approx(1.0)
        assert result.accuracy == pytest.approx(100.0)

    def test_corrected_errors_count_against_accuracy(self) -> None:
        session, clock = make_session("ab", duration=60)
        session.type_char("x")  # wrong
        session.backspace()
        session.type_char("a")
        session.type_char("b")
        clock.advance(60.0)
        session.tick()
        result = session.result()
        assert result.total_keystrokes == 3
        assert result.correct_keystrokes == 2
        assert result.accuracy == pytest.approx(200.0 / 3.0)
        assert result.uncorrected_errors == 0

    def test_uncorrected_errors(self) -> None:
        session, clock = make_session("abc", duration=60)
        session.type_char("axc")
        clock.advance(60.0)
        session.tick()
        assert session.result().uncorrected_errors == 1

    def test_consistency_steady_is_100(self) -> None:
        session, clock = make_session("a" * 50, duration=60)
        for _ in range(12):
            session.type_char("a")
            clock.advance(INTERVAL_SECONDS)
            session.tick()
        result = session.result()
        assert session.finished
        assert result.consistency == pytest.approx(100.0)

    def test_consistency_varied_is_lower(self) -> None:
        session, clock = make_session("a" * 200, duration=60)
        for _ in range(6):
            for _ in range(10):
                session.type_char("a")
                clock.advance(0.1)
            clock.advance(INTERVAL_SECONDS)
            session.tick()
        assert session.result().consistency < 100.0

    def test_intervals_are_5_seconds(self) -> None:
        session, clock = make_session("a" * 100, duration=60)
        for _ in range(30):
            session.type_char("a")
            clock.advance(1.0)
        session.tick()
        intervals = session.result().intervals
        assert intervals
        for interval in intervals:
            assert interval.end - interval.start == pytest.approx(INTERVAL_SECONDS)
        assert interval.wpm == pytest.approx((interval.keystrokes / 5.0) / 0.0833, rel=0.01)


class TestValidity:
    def test_too_short_is_invalid(self) -> None:
        session, clock = make_session("hola mundo entero y largo", duration=60)
        for _ in range(20):
            session.type_char("hola mundo entero y largo"[session.position])
        clock.advance(3.0)
        session.tick()
        result = session.result()
        assert result.valid is False

    def test_too_few_keystrokes_is_invalid(self) -> None:
        session, clock = make_session("hola mundo entero y largo", duration=60)
        for _ in range(5):
            session.type_char("hola mundo"[session.position])
        clock.advance(30.0)
        session.tick()
        assert session.result().valid is False

    def test_valid_test_passes_thresholds(self) -> None:
        session, clock = make_session("a" * 30, duration=60)
        for _ in range(20):
            session.type_char("a")
            clock.advance(0.5)
        session.tick()
        assert session.result().valid is True

    def test_aborted_is_invalid(self) -> None:
        session, clock = make_session("a" * 30, duration=60)
        for _ in range(15):
            session.type_char("a")
            clock.advance(1.0)
        result = session.abort()
        assert result.valid is False
        assert result.aborted is True

    def test_result_to_dict_is_json_serializable(self) -> None:
        import json

        session, clock = make_session("a" * 30, duration=60)
        for _ in range(15):
            session.type_char("a")
            clock.advance(1.0)
        payload = session.result().to_dict()
        assert json.loads(json.dumps(payload)) == payload
        assert payload["duration_seconds"] == 60


class TestKeyStats:
    def test_key_stats_count_errors_and_latency(self) -> None:
        session, clock = make_session("abb", duration=60)
        session.type_char("a")
        clock.advance(1.0)
        session.type_char("x")
        session.backspace()
        clock.advance(1.0)
        session.type_char("b")
        clock.advance(60.0)
        session.tick()
        stats = session.key_stats()
        assert stats["a"].attempts == 1
        assert stats["a"].errors == 0
        assert stats["b"].attempts == 2
        assert stats["b"].errors == 1
        assert stats["b"].avg_latency == pytest.approx(1.0)

    def test_keystroke_log_records_everything(self) -> None:
        session, _ = make_session("ab", duration=60)
        session.type_char("a")
        session.backspace()
        session.type_char("a")
        log = session.keystroke_log()
        assert len(log) == 3
        assert log[1]["is_backspace"] is True
        assert log[2]["correct"] is True

    def test_empty_text_session_is_safe(self) -> None:
        session, _ = make_session("", duration=60)
        session.type_char("a")
        result = session.result()
        assert result.valid is False
        assert result.total_keystrokes == 0
