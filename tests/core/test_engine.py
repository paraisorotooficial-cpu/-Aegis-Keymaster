"""Unit tests for the typing engine."""

from __future__ import annotations

import pytest
from src.core.engine import CharState, TypingEngine


class TestTypingEngine:
    def test_load_resets_state(self) -> None:
        engine = TypingEngine()
        engine.load("casa")
        snap = engine.snapshot()
        assert snap.current_index == 0
        assert snap.chars[0].state == CharState.CURRENT
        assert not snap.finished

    def test_correct_typing_marks_chars(self) -> None:
        engine = TypingEngine()
        engine.load("casa")
        engine.process_text("ca")
        snap = engine.snapshot()
        assert [c.state for c in snap.chars[:2]] == [CharState.CORRECT, CharState.CORRECT]
        assert snap.errors == 0

    def test_wrong_char_is_incorrect(self) -> None:
        engine = TypingEngine()
        engine.load("casa")
        engine.process_text("cxsa")
        snap = engine.snapshot()
        assert snap.errors == 1
        assert snap.chars[1].state == CharState.INCORRECT

    def test_finishes_when_target_reached(self) -> None:
        engine = TypingEngine()
        engine.load("hola")
        engine.process_text("hola")
        assert engine.snapshot().finished

    def test_backspace_allows_correction(self) -> None:
        engine = TypingEngine()
        engine.load("hola")
        engine.process_text("hxla")
        engine.process_text("ho")
        snap = engine.snapshot()
        assert snap.errors == 0
        assert snap.current_index == 2

    def test_empty_load_is_safe(self) -> None:
        engine = TypingEngine()
        engine.load("")
        snap = engine.snapshot()
        assert not snap.finished
        assert snap.wpm == 0.0

    def test_wpm_zero_before_start(self) -> None:
        engine = TypingEngine()
        engine.load("texto de prueba")
        assert engine.snapshot().wpm == 0.0

    @pytest.mark.parametrize("text", ["a", "ñ", "¿", "á"])
    def test_spanish_single_chars(self, text: str) -> None:
        engine = TypingEngine()
        engine.load(text)
        engine.process_text(text)
        snap = engine.snapshot()
        assert snap.finished
        assert snap.errors == 0
