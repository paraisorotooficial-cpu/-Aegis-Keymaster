"""UI smoke tests for the course mode, virtual keyboard and typing composition."""

from __future__ import annotations

import pytest
from src.core.layouts import load_layout
from src.core.lessons import LessonManager
from src.core.weak_keys import KeyStats
from src.ui import themes
from src.ui.course_mode import CoursePage, LessonScreen

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance() or QApplication([])
    return app


@pytest.fixture
def manager() -> LessonManager:
    return LessonManager(layout=load_layout("es"), seed=42)


def test_course_page_builds_and_lists_lessons(qapp, manager) -> None:
    page = CoursePage(manager, themes.ThemeMode.NEON)
    assert page.list_screen._rows_layout.count() == len(manager.lessons)


def test_open_lesson_and_type(qapp, manager) -> None:
    page = CoursePage(manager, themes.ThemeMode.NEON)
    page._open_lesson("L01")
    screen = page.lesson_screen
    assert screen._text
    QTest.keyClicks(screen._typing_area, screen._text[:20])
    assert len(screen._typed) == 20
    assert screen._typing_area._states[:20] == ["correct"] * 20


def test_lesson_finish_emits_result(qapp, manager) -> None:
    page = CoursePage(manager, themes.ThemeMode.NEON)
    results: list[tuple] = []
    page.lesson_completed.connect(lambda *args: results.append(args))
    page._open_lesson("L01")
    screen = page.lesson_screen
    QTest.keyClicks(screen._typing_area, screen._text)
    assert len(results) == 1
    lesson_id, _wpm, _accuracy, _stars, key_stats = results[0]
    assert lesson_id == "L01"
    assert key_stats and isinstance(next(iter(key_stats.values())), KeyStats)


def test_review_flow_does_not_emit_lesson_result(qapp, manager) -> None:
    page = CoursePage(manager, themes.ThemeMode.NEON)
    results: list = []
    reviews: list = []
    page.lesson_completed.connect(lambda *args: results.append(args))
    page.lesson_screen.review_finished.connect(lambda stats: reviews.append(stats))
    page.open_review("asdf jkl; asdf jkl;")
    QTest.keyClicks(page.lesson_screen._typing_area, "asdf jkl; asdf jkl;")
    assert not results
    assert len(reviews) == 1


def test_virtual_keyboard_highlights_target(qapp) -> None:
    from src.ui.virtual_keyboard import VirtualKeyboard

    keyboard = VirtualKeyboard("latam")
    keyboard.set_target("á")
    assert keyboard._modifier_flag == "dead"
    keyboard.set_target("@")
    assert keyboard._modifier_flag == "altgr"
    keyboard.set_target("A")
    assert keyboard._modifier_flag == "shift"
    keyboard.set_target("a")
    assert keyboard._modifier_flag == ""
    pixmap = keyboard.grab()
    assert not pixmap.isNull()


def test_virtual_keyboard_uses_layout_data(qapp) -> None:
    from src.ui.virtual_keyboard import VirtualKeyboard

    keyboard = VirtualKeyboard("us")
    keyboard.set_target("ñ")
    assert keyboard._modifier_flag == ""  # ñ missing on us: no highlight state crash
    keyboard.set_layout("es")
    keyboard.set_target("ñ")
    assert keyboard._modifier_flag == ""  # ñ is a plain key on es


def _press_key(widget, text: str) -> None:
    event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier, text)
    widget.keyPressEvent(event)


def test_dead_key_composition_in_typing_area(qapp, manager) -> None:
    screen = LessonScreen(manager, themes.ThemeMode.NEON)
    screen.start_review("áé test", load_layout("es"))
    area = screen._typing_area
    _press_key(area, "´")
    _press_key(area, "a")
    _press_key(area, "´")
    _press_key(area, "é")
    QTest.keyClicks(area, " test")
    assert screen._typed == "áé test"


def test_dead_key_plus_space_emits_dead_char(qapp, manager) -> None:
    screen = LessonScreen(manager, themes.ThemeMode.NEON)
    screen.start_review("´ a", load_layout("es"))
    area = screen._typing_area
    _press_key(area, "´")
    _press_key(area, " ")
    assert screen._typed == "´"


def test_dead_key_with_unknown_base_falls_back(qapp, manager) -> None:
    screen = LessonScreen(manager, themes.ThemeMode.NEON)
    screen.start_review("´x", load_layout("es"))
    area = screen._typing_area
    _press_key(area, "´")
    _press_key(area, "x")
    assert screen._typed == "x"


def test_backspace_cancels_pending_dead_key(qapp, manager) -> None:
    screen = LessonScreen(manager, themes.ThemeMode.NEON)
    screen.start_review("a", load_layout("es"))
    area = screen._typing_area
    _press_key(area, "´")
    QTest.keyClick(area, Qt.Key.Key_Backspace)
    _press_key(area, "a")
    assert screen._typed == "a"


def test_dead_key_press_not_counted_as_keystroke(qapp, manager) -> None:
    screen = LessonScreen(manager, themes.ThemeMode.NEON)
    screen.start_review("á", load_layout("es"))
    _press_key(screen._typing_area, "´")
    assert screen._typed == ""
    assert not screen._key_stats
    _press_key(screen._typing_area, "a")
    assert screen._typed == "á"
    stats = screen._key_stats["á"]
    assert stats.attempts == 1
    assert stats.errors == 0
