"""Timed typing test session — pure logic, no Qt.

Implements the brief §7.2 contract:

- ``TypingTestSession(text, duration_seconds, clock, min_attempts)``
  with allowed durations 60, 180 and 300 seconds and an injectable clock.
- The timer starts on the first keystroke.
- The test does not block on errors: the cursor advances and backspace is
  allowed (a blocking mode is a separate UI setting, handled outside).
- Definitions: 1 word = 5 characters; gross WPM = typed characters / 5 /
  minutes; net WPM = correct characters on screen / 5 / minutes;
  accuracy = correct keystrokes / total keystrokes (corrected errors still
  count against accuracy); consistency = 100 - coefficient of variation of
  the per-5-second-interval speed.
- A test is invalid (``valid = False``) if it lasts less than 5 seconds or
  has fewer than 10 keystrokes; invalid tests must not be saved.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

ALLOWED_DURATIONS: tuple[int, ...] = (60, 180, 300)
MIN_VALID_SECONDS = 5.0
MIN_VALID_ATTEMPTS = 10
INTERVAL_SECONDS = 5.0

BACKSPACE = "\b"


class InvalidDurationError(ValueError):
    """Raised when a test duration is not one of the allowed values."""


@dataclass(frozen=True)
class Keystroke:
    """One recorded character attempt (backspaces are recorded too)."""

    position: int
    expected: str
    typed: str
    correct: bool
    offset: float  # seconds since the timer started
    is_backspace: bool = False


@dataclass(frozen=True)
class IntervalStat:
    """Typing speed within one 5-second interval."""

    start: float
    end: float
    keystrokes: int
    correct: int
    wpm: float


@dataclass
class TestResult:
    """Immutable summary of a finished (or aborted) test."""

    text: str
    typed_text: str
    duration_seconds: int
    elapsed_seconds: float
    total_keystrokes: int
    correct_keystrokes: int
    uncorrected_errors: int
    gross_wpm: float
    net_wpm: float
    accuracy: float
    consistency: float
    valid: bool
    aborted: bool
    intervals: list[IntervalStat] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable representation."""
        return {
            "text": self.text,
            "typed_text": self.typed_text,
            "duration_seconds": self.duration_seconds,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "total_keystrokes": self.total_keystrokes,
            "correct_keystrokes": self.correct_keystrokes,
            "uncorrected_errors": self.uncorrected_errors,
            "gross_wpm": round(self.gross_wpm, 2),
            "net_wpm": round(self.net_wpm, 2),
            "accuracy": round(self.accuracy, 2),
            "consistency": round(self.consistency, 2),
            "valid": self.valid,
            "aborted": self.aborted,
            "intervals": [
                {
                    "start": round(i.start, 3),
                    "end": round(i.end, 3),
                    "keystrokes": i.keystrokes,
                    "correct": i.correct,
                    "wpm": round(i.wpm, 2),
                }
                for i in self.intervals
            ],
        }


@dataclass
class KeyAttempt:
    """Aggregated per-key statistics for one test."""

    attempts: int = 0
    errors: int = 0
    latency_total: float = 0.0
    latency_samples: int = 0

    @property
    def error_rate(self) -> float:
        return self.errors / self.attempts if self.attempts else 0.0

    @property
    def avg_latency(self) -> float:
        return self.latency_total / self.latency_samples if self.latency_samples else 0.0


class TypingTestSession:
    """Keystroke-level timed typing test with an injectable clock."""

    def __init__(
        self,
        text: str,
        duration_seconds: int,
        clock: Callable[[], float] | None = None,
        min_attempts: int = MIN_VALID_ATTEMPTS,
    ) -> None:
        if duration_seconds not in ALLOWED_DURATIONS:
            raise InvalidDurationError(
                f"duration must be one of {ALLOWED_DURATIONS}, got {duration_seconds}"
            )
        self.text = text
        self.duration_seconds = duration_seconds
        self.clock: Callable[[], float] = clock or time.perf_counter
        self.min_attempts = min_attempts

        self._started_at: float | None = None
        self._now: float = 0.0
        self._position = 0
        self._states: list[str] = ["pending"] * len(text)
        self._keystrokes: list[Keystroke] = []
        self._finished = False
        self._aborted = False

    # -- input -----------------------------------------------------

    def type_char(self, char: str) -> None:
        """Record one character attempt at the cursor position."""
        if self._finished or self._aborted or not char:
            return
        self._ensure_started()
        self._now = self.clock()
        if self._position >= len(self.text):
            return

        expected = self.text[self._position]
        correct = char == expected
        offset = self._now - self._started_at  # type: ignore[operator]
        self._keystrokes.append(
            Keystroke(self._position, expected, char, correct, offset, is_backspace=False)
        )
        self._states[self._position] = "correct" if correct else "incorrect"
        self._position += 1
        self._check_time()

    def backspace(self) -> bool:
        """Move the cursor back and clear the char state. Returns True if moved."""
        if self._finished or self._aborted or self._position == 0:
            return False
        self._ensure_started()
        self._now = self.clock()
        self._position -= 1
        self._states[self._position] = "pending"
        offset = self._now - self._started_at  # type: ignore[operator]
        self._keystrokes.append(
            Keystroke(self._position, self.text[self._position], BACKSPACE, False, offset,
                      is_backspace=True)
        )
        self._check_time()
        return True

    def tick(self, now: float | None = None) -> bool:
        """Advance the clock; returns True when the test just finished."""
        if self._started_at is None or self._finished:
            return False
        self._now = self.clock() if now is None else now
        return self._check_time()

    def extend(self, extra_text: str) -> None:
        """Append text so a fast typist does not run out before the timer."""
        if self._finished or self._aborted or not extra_text:
            return
        self.text += extra_text
        self._states.extend(["pending"] * len(extra_text))

    def abort(self) -> TestResult:
        """Finish the test early. Aborted tests are always invalid."""
        self._aborted = True
        self._finished = True
        return self.result()

    # -- state -----------------------------------------------------

    @property
    def position(self) -> int:
        return self._position

    @property
    def states(self) -> list[str]:
        return list(self._states)

    @property
    def started(self) -> bool:
        return self._started_at is not None

    @property
    def finished(self) -> bool:
        return self._finished

    @property
    def elapsed(self) -> float:
        if self._started_at is None:
            return 0.0
        return max(0.0, self._now - self._started_at)

    @property
    def remaining(self) -> float:
        return max(0.0, self.duration_seconds - self.elapsed)

    def live_wpm(self) -> float:
        """Net WPM so far, based on correct characters on screen."""
        minutes = self.elapsed / 60.0
        if minutes <= 0:
            return 0.0
        correct = sum(1 for s in self._states if s == "correct")
        return (correct / 5.0) / minutes

    # -- results ---------------------------------------------------

    def result(self) -> TestResult:
        elapsed = min(self.elapsed, float(self.duration_seconds))
        attempts = [k for k in self._keystrokes if not k.is_backspace]
        total = len(attempts)
        correct = sum(1 for k in attempts if k.correct)
        correct_on_screen = sum(1 for s in self._states if s == "correct")
        minutes = elapsed / 60.0
        gross = (total / 5.0) / minutes if minutes > 0 else 0.0
        net = (correct_on_screen / 5.0) / minutes if minutes > 0 else 0.0
        accuracy = 100.0 * correct / total if total else 0.0
        intervals = self._intervals()
        consistency = self._consistency(intervals)
        valid = (
            not self._aborted
            and elapsed >= MIN_VALID_SECONDS
            and total >= self.min_attempts
        )
        return TestResult(
            text=self.text,
            typed_text=self.text[: self._position],
            duration_seconds=self.duration_seconds,
            elapsed_seconds=elapsed,
            total_keystrokes=total,
            correct_keystrokes=correct,
            uncorrected_errors=sum(1 for s in self._states if s == "incorrect"),
            gross_wpm=gross,
            net_wpm=net,
            accuracy=accuracy,
            consistency=consistency,
            valid=valid,
            aborted=self._aborted,
            intervals=intervals,
        )

    def key_stats(self) -> dict[str, KeyAttempt]:
        """Per-key attempts, errors and average latency for this test."""
        stats: dict[str, KeyAttempt] = {}
        previous_offset: float | None = None
        for k in self._keystrokes:
            if k.is_backspace:
                continue
            entry = stats.setdefault(k.expected, KeyAttempt())
            entry.attempts += 1
            if not k.correct:
                entry.errors += 1
            if previous_offset is not None:
                latency = k.offset - previous_offset
                if latency >= 0:
                    entry.latency_total += latency
                    entry.latency_samples += 1
            previous_offset = k.offset
        return stats

    def keystroke_log(self) -> list[dict[str, Any]]:
        """Per-keystroke records for the weak-key tracker."""
        return [
            {
                "expected": k.expected,
                "typed": k.typed,
                "correct": k.correct,
                "offset": round(k.offset, 4),
                "is_backspace": k.is_backspace,
            }
            for k in self._keystrokes
        ]

    # -- internals -------------------------------------------------

    def _ensure_started(self) -> None:
        if self._started_at is None:
            self._started_at = self.clock()
            self._now = self._started_at

    def _check_time(self) -> bool:
        if self._started_at is None or self._finished:
            return False
        if self.elapsed >= self.duration_seconds:
            self._finished = True
            return True
        return False

    def _intervals(self) -> list[IntervalStat]:
        attempts = [k for k in self._keystrokes if not k.is_backspace]
        if not attempts:
            return []
        elapsed = min(self.elapsed, float(self.duration_seconds))
        span = max(elapsed, math.ceil(attempts[-1].offset) + 1)
        count = math.ceil(span / INTERVAL_SECONDS)
        per_interval: list[list[int]] = [[0, 0] for _ in range(count)]
        for k in attempts:
            idx = min(int(k.offset // INTERVAL_SECONDS), count - 1)
            per_interval[idx][0] += 1
            if k.correct:
                per_interval[idx][1] += 1
        result = []
        for i, (total_i, correct_i) in enumerate(per_interval):
            start = i * INTERVAL_SECONDS
            result.append(
                IntervalStat(
                    start=start,
                    end=start + INTERVAL_SECONDS,
                    keystrokes=total_i,
                    correct=correct_i,
                    wpm=(total_i / 5.0) / (INTERVAL_SECONDS / 60.0),
                )
            )
        return result

    @staticmethod
    def _consistency(intervals: list[IntervalStat]) -> float:
        speeds = [i.wpm for i in intervals]
        if len(speeds) < 2:
            return 100.0
        mean = sum(speeds) / len(speeds)
        if mean <= 0:
            return 0.0
        variance = sum((s - mean) ** 2 for s in speeds) / (len(speeds) - 1)
        cv = math.sqrt(variance) / mean
        return max(0.0, 100.0 - cv * 100.0)
