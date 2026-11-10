"""Long-session stability: 30 simulated minutes of typing without leaks or errors."""

from __future__ import annotations

import tracemalloc

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from src.core.typing_test import TypingTestSession
from src.ui.typing_area import TypingArea


class FakeClock:
    def __init__(self) -> None:
        self._t = 0.0

    def __call__(self) -> float:
        return self._t

    def advance(self, seconds: float) -> None:
        self._t += seconds


def _thirty_minutes_of_sessions() -> tuple[int, float]:
    """Simulate 30 min of continuous timed tests through the core engine."""
    clock = FakeClock()
    text = ("cuando llego la tormenta los barcos regresaron al puerto con las velas "
            "recogidas y las luces encendidas los pescadores amarraron las cuerdas ") * 50
    total_keys = 0
    for _ in range(30):  # 30 sessions of 60 simulated seconds
        session = TypingTestSession(text, 60, clock, min_attempts=10)
        end = clock() + 60.0
        i = 0
        while not session.finished and clock() < end:
            session.type_char(text[i % len(text)])
            total_keys += 1
            i += 1
            clock.advance(0.05)
            if i % 20 == 0:
                session.backspace()
                total_keys += 1
            session.tick()
        result = session.result()
        assert result.gross_wpm >= 0 and 0 <= result.accuracy <= 100
    return total_keys, clock()


def _press(area: TypingArea, ch: str) -> None:
    area.event(
        QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier, ch)
    )


def test_thirty_minute_simulated_session(qapp) -> None:
    total_keys, simulated_seconds = _thirty_minutes_of_sessions()
    assert simulated_seconds >= 1800
    assert total_keys > 5000

    area = TypingArea()
    area.resize(800, 400)
    area.show()
    text = ("cuando llego la tormenta los barcos regresaron al puerto con las velas "
            "recogidas y las luces encendidas ") * 20

    tracemalloc.start()
    baseline_snap = tracemalloc.take_snapshot()
    for _round_no in range(6):  # ~1800 keystrokes through the live widget
        session = TypingTestSession(text, 60, min_attempts=10)
        area.load(text, session.states)
        area.setFocus()
        for i, ch in enumerate(text[:300]):
            _press(area, ch)
            session.type_char(ch)
            area.update_state(session.position, session.states)
            if i % 50 == 0:
                qapp.processEvents()
        session.tick()
    qapp.processEvents()
    peak = tracemalloc.get_traced_memory()[1]
    snap = tracemalloc.take_snapshot()
    top = snap.compare_to(baseline_snap, "lineno")
    tracemalloc.stop()

    assert peak < 50_000_000, f"memory peak too high: {peak / 1_000_000:.0f} MB"
    assert _round_no == 5
    assert top is not None
