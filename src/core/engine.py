"""
Typing engine — real-time WPM, accuracy, error tracking and character-level state.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto


class CharState(Enum):
    PENDING = auto()
    CORRECT = auto()
    INCORRECT = auto()
    CURRENT = auto()


@dataclass
class CharInfo:
    char: str
    state: CharState = CharState.PENDING


@dataclass
class EngineSnapshot:
    """Immutable view of engine state for the UI."""
    target: str
    typed: str
    chars: list[CharInfo]
    wpm: float
    accuracy: float          # 0-100
    errors: int
    correct: int
    elapsed_seconds: float
    finished: bool
    current_index: int


class TypingEngine:
    """
    Core logic for a typing session.

    - Accepts a target text
    - Processes keystrokes (or full text from a QTextEdit)
    - Computes live WPM, accuracy and error count
    - Maintains per-character state for visual feedback
    """

    def __init__(self):
        self._target: str = ""
        self._typed: str = ""
        self._chars: list[CharInfo] = []
        self._start_time: float | None = None
        self._finished: bool = False
        self._errors: int = 0
        self._on_update: Callable[[EngineSnapshot], None] | None = None

    # -- Public API -------------------------------

    def set_on_update(self, callback: Callable[[EngineSnapshot], None]):
        self._on_update = callback

    def load(self, target: str):
        """Load a new target text and reset session."""
        self._target = target
        self._typed = ""
        self._chars = [CharInfo(c) for c in target]
        if self._chars:
            self._chars[0].state = CharState.CURRENT
        self._start_time = None
        self._finished = False
        self._errors = 0
        self._emit()

    def reset(self):
        self.load(self._target)

    def process_text(self, typed: str):
        """
        Process the full current typed text (from QPlainTextEdit).
        This is the primary update path for the UI.
        """
        if self._finished and typed.startswith(self._typed):
            return

        if self._start_time is None and typed:
            self._start_time = time.perf_counter()

        self._typed = typed
        self._recompute_states()
        self._emit()

    def snapshot(self) -> EngineSnapshot:
        return self._make_snapshot()

    # -- Internals -------------------------------─

    def _recompute_states(self):
        target = self._target
        typed = self._typed
        n_target = len(target)
        n_typed = len(typed)

        errors = 0
        correct = 0
        self._finished = n_target > 0 and n_typed >= n_target

        for i, info in enumerate(self._chars):
            if i < n_typed:
                if typed[i] == target[i]:
                    info.state = CharState.CORRECT
                    correct += 1
                else:
                    info.state = CharState.INCORRECT
                    errors += 1
            elif i == n_typed and not self._finished:
                info.state = CharState.CURRENT
            else:
                info.state = CharState.PENDING

        self._errors = errors

    def _elapsed(self) -> float:
        if self._start_time is None:
            return 0.0
        return max(0.0, time.perf_counter() - self._start_time)

    def _wpm(self) -> float:
        """
        Standard net WPM: (correct characters / 5) / minutes.
        Uses only correctly typed characters.
        """
        elapsed = self._elapsed()
        if elapsed < 0.3:
            return 0.0
        correct_chars = sum(1 for c in self._chars if c.state == CharState.CORRECT)
        minutes = elapsed / 60.0
        return round((correct_chars / 5.0) / minutes, 1)

    def _accuracy(self) -> float:
        total = len(self._typed)
        if total == 0:
            return 100.0
        correct = sum(1 for c in self._chars if c.state == CharState.CORRECT)
        # Accuracy over characters that have been attempted
        attempted = min(total, len(self._target))
        if attempted == 0:
            return 100.0
        return round(100.0 * correct / attempted, 1)

    def _make_snapshot(self) -> EngineSnapshot:
        correct = sum(1 for c in self._chars if c.state == CharState.CORRECT)
        current_idx = next(
            (i for i, c in enumerate(self._chars) if c.state == CharState.CURRENT),
            len(self._chars)
        )
        return EngineSnapshot(
            target=self._target,
            typed=self._typed,
            chars=list(self._chars),
            wpm=self._wpm(),
            accuracy=self._accuracy(),
            errors=self._errors,
            correct=correct,
            elapsed_seconds=self._elapsed(),
            finished=self._finished,
            current_index=current_idx,
        )

    def _emit(self):
        if self._on_update:
            self._on_update(self._make_snapshot())
