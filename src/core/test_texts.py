"""Load and pick timed-test texts by language."""

from __future__ import annotations

import json
import random
from importlib import resources
from typing import Any

SUPPORTED_LANGUAGES = ("es", "en")
MIN_CHARS_FOR_5_MINUTES = 1600


class TestTextBank:
    """Holds practice texts per language and picks them for a duration."""

    def __init__(self, data: dict[str, list[str]] | None = None, seed: int | None = None) -> None:
        if data is None:
            data = _load_default()
        self._texts = {lang: list(texts) for lang, texts in data.items() if texts}
        self._rng = random.Random(seed)

    def languages(self) -> tuple[str, ...]:
        return tuple(sorted(self._texts))

    def pick(self, language: str, duration_seconds: int) -> str:
        """Return a text long enough for the given duration."""
        if language not in self._texts:
            raise KeyError(f"unsupported language {language!r}; have {self.languages()}")
        text = self._rng.choice(self._texts[language])
        needed = _chars_needed(duration_seconds)
        while len(text) < needed:
            text += " " + self._rng.choice(self._texts[language])
        return text


def _chars_needed(duration_seconds: int) -> int:
    worst_case_wpm = 80
    return int(duration_seconds / 60.0 * worst_case_wpm * 5)


def _load_default() -> dict[str, list[str]]:
    raw: Any = json.loads(
        resources.files("src.data").joinpath("test_texts.json").read_text(encoding="utf-8")
    )
    return {lang: list(texts) for lang, texts in raw.items()}
