"""Tests for test-text loading and picking."""

from __future__ import annotations

import pytest
from src.core.test_texts import TestTextBank as TextsFactory


@pytest.fixture(scope="module")
def texts() -> TextsFactory:
    return TextsFactory(seed=42)


class TestTextsFactory:
    def test_default_languages(self, texts: TextsFactory) -> None:
        assert "es" in texts.languages()
        assert "en" in texts.languages()

    def test_pick_returns_text(self, texts: TextsFactory) -> None:
        text = texts.pick("es", 60)
        assert len(text) > 100

    def test_pick_long_enough_for_5_minutes(self, texts: TextsFactory) -> None:
        text = texts.pick("es", 300)
        assert len(text) >= 1600

    def test_pick_unknown_language_raises(self, texts: TextsFactory) -> None:
        with pytest.raises(KeyError):
            texts.pick("fr", 60)

    def test_empty_data_has_no_languages(self) -> None:
        assert TextsFactory(data={}).languages() == ()
