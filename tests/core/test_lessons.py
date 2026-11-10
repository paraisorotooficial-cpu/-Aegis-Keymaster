"""Tests for the structured course (lessons, unlocks, stars, text generation)."""

from __future__ import annotations

import pytest
from src.core.layouts import load_layout
from src.core.lessons import LESSON_LENGTH_CHARS, LessonManager

PROGRESS = {
    "L01": {"stars": 2, "best_wpm": 22, "best_accuracy": 95},
    "L02": {"stars": 1, "best_wpm": 17, "best_accuracy": 91},
}


def test_fifteen_lessons_loaded() -> None:
    manager = LessonManager()
    assert len(manager.lessons) == 15
    assert manager.lessons[0].id == "L01"
    assert manager.lessons[-1].id == "L15"


def test_first_lesson_unlocked_others_locked() -> None:
    manager = LessonManager()
    assert manager.is_unlocked(manager.lessons[0], {})
    assert not manager.is_unlocked(manager.lessons[1], {})


def test_unlock_chain_requires_previous_pass() -> None:
    manager = LessonManager()
    assert manager.is_unlocked(manager.lessons[1], PROGRESS)
    assert manager.is_unlocked(manager.lessons[2], PROGRESS)
    assert not manager.is_unlocked(manager.lessons[3], PROGRESS)


def test_unlocked_keys_accumulate() -> None:
    manager = LessonManager()
    keys = manager.unlocked_keys(PROGRESS)
    assert {"a", "s", "d", "f", "j", "k", "l"} <= keys
    assert {"g", "h", "ñ"} <= keys
    assert "e" not in keys


def test_stars_zero_when_below_pass() -> None:
    manager = LessonManager()
    lesson = manager.lessons[0]
    assert manager.stars_for(lesson, lesson.min_wpm - 1, 99) == 0
    assert manager.stars_for(lesson, lesson.min_wpm, 89) == 0


def test_stars_one_two_three() -> None:
    manager = LessonManager()
    lesson = manager.lessons[0]
    assert manager.stars_for(lesson, lesson.min_wpm + 0.1, 91) == 1
    assert manager.stars_for(lesson, lesson.min_wpm * 1.25, 91) == 2
    assert manager.stars_for(lesson, lesson.min_wpm * 1.45, 91) == 3


def test_record_result_keeps_best_and_max_stars() -> None:
    manager = LessonManager()
    lesson = manager.lessons[0]
    progress: dict = {}
    entry = manager.record_result(lesson, 20.0, 92.0, progress)
    assert entry["stars"] == 2
    entry = manager.record_result(lesson, 18.0, 91.0, progress)
    assert entry["stars"] == 2
    assert entry["best_wpm"] == 20.0
    assert entry["best_accuracy"] == 92.0


def test_failed_result_gives_zero_stars_but_records() -> None:
    manager = LessonManager()
    lesson = manager.lessons[0]
    progress: dict = {}
    entry = manager.record_result(lesson, 5.0, 60.0, progress)
    assert entry["stars"] == 0
    assert entry["best_wpm"] == 5.0


def test_lesson_text_only_uses_unlocked_keys() -> None:
    manager = LessonManager(layout=load_layout("es"), seed=7)
    text = manager.lesson_text(manager.lessons[0], {})
    assert text
    assert set(text.lower()) <= set("asdfjkl ")


def test_lesson_text_length_target() -> None:
    manager = LessonManager(layout=load_layout("es"), seed=7)
    text = manager.lesson_text(manager.lessons[0], {}, length=LESSON_LENGTH_CHARS)
    assert len(text) >= LESSON_LENGTH_CHARS * 0.9


def test_lesson_text_with_caps() -> None:
    manager = LessonManager(layout=load_layout("es"), seed=3)
    lesson = manager.lessons[7]
    text = manager.lesson_text(lesson, PROGRESS)
    assert set(text) <= set("".join(manager.unlocked_keys(PROGRESS)) + " " + "".join(
        c.upper() for c in manager.unlocked_keys(PROGRESS)
    ))


def test_lesson_text_accent_lesson_includes_accents() -> None:
    manager = LessonManager(layout=load_layout("es"), seed=5)
    lesson = manager.lessons[11]
    text = manager.lesson_text(lesson, PROGRESS)
    assert any(c in text for c in "áéíóú")


def test_drill_fallback_when_no_words() -> None:
    words = ["zzz"]  # unusable, forces drill path
    manager = LessonManager(words=words, layout=load_layout("es"), seed=1)
    text = manager.lesson_text(manager.lessons[0], {})
    assert text
    assert set(text.lower()) <= set("asdfjkl ")


def test_next_lesson_progression() -> None:
    manager = LessonManager()
    assert manager.next_lesson({}).id == "L01"
    assert manager.next_lesson(PROGRESS).id == "L03"
    full = {f"L{i:02d}": {"stars": 3} for i in range(1, 16)}
    assert manager.next_lesson(full) is None


def test_course_completable_start_to_finish() -> None:
    manager = LessonManager(layout=load_layout("es"), seed=11)
    progress: dict = {}
    for lesson in manager.lessons:
        assert manager.is_unlocked(lesson, progress)
        text = manager.lesson_text(lesson, progress)
        assert len(text) >= 100
        manager.record_result(lesson, lesson.min_wpm + 1, lesson.min_accuracy + 1, progress)
    assert manager.next_lesson(progress) is None


@pytest.mark.parametrize("layout_name", ["us", "es", "latam"])
def test_texts_work_on_every_layout(layout_name: str) -> None:
    manager = LessonManager(layout=load_layout(layout_name), seed=2)
    for lesson in manager.lessons:
        assert manager.lesson_text(lesson, {})
