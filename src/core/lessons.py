"""Structured course: lessons, unlock chain, star ratings and text generation."""

from __future__ import annotations

import json
import random
import string
from dataclasses import dataclass
from importlib import resources
from typing import Any

from src.core.layouts import KeyboardLayout, load_layout

LESSON_LENGTH_CHARS = 360


@dataclass(frozen=True)
class Lesson:
    id: str
    index: int
    title: str
    new_keys: tuple[str, ...]
    min_wpm: float
    min_accuracy: float
    allow_caps: bool = False


def _load_json(package: str, filename: str) -> dict[str, Any]:
    text = (resources.files(package) / filename).read_text(encoding="utf-8")
    return json.loads(text)


class LessonManager:
    """Load lessons from data, manage unlocks, stars and text generation."""

    def __init__(
        self,
        data: dict[str, Any] | None = None,
        words: list[str] | None = None,
        layout: KeyboardLayout | None = None,
        seed: int | None = None,
    ) -> None:
        raw = data if data is not None else _load_json("src.data", "lessons.json")
        margins = raw.get("star_margins", {"two": 1.2, "three": 1.4})
        self._star_two = float(margins.get("two", 1.2))
        self._star_three = float(margins.get("three", 1.4))
        self.lessons: list[Lesson] = [
            Lesson(
                id=item["id"],
                index=i,
                title=item["title"],
                new_keys=tuple(item.get("new_keys", ())),
                min_wpm=float(item.get("min_wpm", 15)),
                min_accuracy=float(item.get("min_accuracy", 90)),
                allow_caps=bool(item.get("allow_caps", False)),
            )
            for i, item in enumerate(raw["lessons"])
        ]
        if words is None:
            words = _load_json("src.data", "words_es.json").get("words", [])
        self._words = [w for w in words if w and " " not in w]
        self.layout = layout or load_layout("es")
        self._rng = random.Random(seed)

    # -- unlock chain ---------------------------------------------------

    def is_unlocked(self, lesson: Lesson, progress: dict[str, Any]) -> bool:
        if lesson.index == 0:
            return True
        previous = self.lessons[lesson.index - 1]
        entry = progress.get(previous.id)
        return bool(entry and entry.get("stars", 0) >= 1)

    def unlocked_keys(self, progress: dict[str, Any]) -> set[str]:
        keys: set[str] = set()
        for lesson in self.lessons:
            entry = progress.get(lesson.id)
            if entry and entry.get("stars", 0) >= 1:
                keys.update(lesson.new_keys)
        keys.update(self.lessons[0].new_keys)
        return keys

    def next_lesson(self, progress: dict[str, Any]) -> Lesson | None:
        for lesson in self.lessons:
            if not self.is_unlocked(lesson, progress):
                return lesson
            entry = progress.get(lesson.id)
            if not entry or entry.get("stars", 0) < 1:
                return lesson
        return None

    # -- stars ----------------------------------------------------------

    def stars_for(self, lesson: Lesson, wpm: float, accuracy: float) -> int:
        if wpm < lesson.min_wpm or accuracy < lesson.min_accuracy:
            return 0
        if wpm >= lesson.min_wpm * self._star_three and accuracy >= lesson.min_accuracy:
            return 3
        if wpm >= lesson.min_wpm * self._star_two and accuracy >= lesson.min_accuracy:
            return 2
        return 1

    def record_result(
        self, lesson: Lesson, wpm: float, accuracy: float, progress: dict[str, Any]
    ) -> dict[str, Any]:
        """Update progress with a result; returns the updated entry."""
        stars = self.stars_for(lesson, wpm, accuracy)
        entry = progress.get(lesson.id) or {}
        updated = {
            "stars": max(stars, int(entry.get("stars", 0))),
            "best_wpm": max(float(entry.get("best_wpm", 0.0)), wpm),
            "best_accuracy": max(float(entry.get("best_accuracy", 0.0)), accuracy),
        }
        progress[lesson.id] = updated
        return updated

    # -- text generation --------------------------------------------------

    def lesson_text(
        self, lesson: Lesson, progress: dict[str, Any], length: int = LESSON_LENGTH_CHARS
    ) -> str:
        unlocked = self._unlocked_for_lesson(lesson, progress)
        words = [w for w in self._words if set(w.lower()) <= unlocked]
        if len(words) >= 6:
            pieces: list[str] = []
            total = 0
            while total < length:
                word = self._rng.choice(words)
                if lesson.allow_caps and self._rng.random() < 0.25:
                    word = word.capitalize()
                pieces.append(word)
                total += len(word) + 1
            return " ".join(pieces)
        return self._drill_text(unlocked, lesson, length)

    def _unlocked_for_lesson(self, lesson: Lesson, progress: dict[str, Any]) -> set[str]:
        keys = {c for c in self.unlocked_keys(progress) if self.layout.can_type(c) or c == " "}
        keys.update(k for k in lesson.new_keys if self.layout.can_type(k))
        keys.add(" ")
        if lesson.allow_caps:
            keys.update(c.upper() for c in list(keys))
        return keys

    def _drill_text(self, unlocked: set[str], lesson: Lesson, length: int) -> str:
        letters = sorted(c for c in unlocked if c in string.ascii_lowercase or c in "ñáéíóúü")
        pool = letters or list(lesson.new_keys) or ["a"]
        pieces: list[str] = []
        total = 0
        while total < length:
            group = "".join(self._rng.choice(pool) for _ in range(self._rng.randint(2, 4)))
            pieces.append(group)
            total += len(group) + 1
        return " ".join(pieces)
