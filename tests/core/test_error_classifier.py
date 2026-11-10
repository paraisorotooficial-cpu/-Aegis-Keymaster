"""Unit tests for keystroke error classification."""

from __future__ import annotations

import pytest
from src.core.error_classifier import ErrorInfo, classify_keystroke


class TestClassifyKeystroke:
    def test_correct_is_none(self) -> None:
        info = classify_keystroke("a", "a")
        assert info.category == "none"
        assert not info.is_error

    def test_case_slip(self) -> None:
        info = classify_keystroke("A", "a")
        assert info.category == "case"
        assert info.is_error

    def test_adjacent_slip(self) -> None:
        info = classify_keystroke("d", "f")
        assert info.category == "adjacent"
        assert info.adjacent

    def test_adjacent_is_symmetric(self) -> None:
        assert classify_keystroke("f", "d").adjacent
        assert classify_keystroke("d", "f").adjacent

    @pytest.mark.parametrize("expected,typed", [("e", "r"), ("n", "m"), ("o", "i"), ("7", "8")])
    def test_common_adjacent_pairs(self, expected: str, typed: str) -> None:
        assert classify_keystroke(expected, typed).category == "adjacent"

    def test_spanish_keys(self) -> None:
        assert classify_keystroke("ñ", "m").category == "adjacent"
        assert classify_keystroke("á", "a").category == "other"

    def test_far_key_is_other(self) -> None:
        assert classify_keystroke("q", "p").category == "other"

    def test_empty_inputs_are_other(self) -> None:
        assert classify_keystroke("a", "").category == "other"
        assert classify_keystroke("", "a").category == "other"

    def test_info_carries_keys(self) -> None:
        info: ErrorInfo = classify_keystroke("A", "a")
        assert info.expected == "A"
        assert info.typed == "a"
