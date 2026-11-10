"""Course mode UI: lesson list, lesson practice screen and results."""

from __future__ import annotations

import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.core.layouts import KeyboardLayout, load_layout
from src.core.lessons import Lesson, LessonManager
from src.core.sound import SoundId
from src.core.weak_keys import KeyStats
from src.ui import themes
from src.ui.fonts import subtitle_font, title_font
from src.ui.typing_area import TypingArea
from src.ui.virtual_keyboard import VirtualKeyboard


def stars_label(stars: int) -> str:
    return "★" * stars + "☆" * (3 - stars)


class LessonRow(QFrame):
    """One lesson entry in the course list."""

    clicked = Signal(str)

    def __init__(self, lesson: Lesson, stars: int, unlocked: bool) -> None:
        super().__init__()
        self._lesson_id = lesson.id
        self.setObjectName("LessonRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        row = QHBoxLayout(self)
        title = QLabel(f"{lesson.index + 1}. {lesson.title}")
        goal = QLabel(f"{lesson.min_wpm:.0f} WPM · {lesson.min_accuracy:.0f} %")
        goal.setObjectName("Muted")
        state = QLabel(stars_label(stars) if unlocked else "🔒")
        state.setObjectName("Subtitle")
        state.setFont(subtitle_font())
        row.addWidget(title, 1)
        row.addWidget(goal)
        row.addWidget(state)
        if unlocked:
            row.addWidget(self._start_button())

    def _start_button(self) -> QPushButton:
        button = QPushButton("Empezar")
        button.clicked.connect(lambda _=False: self.clicked.emit(self._lesson_id))
        return button

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self._lesson_id)


class CourseListScreen(QWidget):
    """Course overview: unlock chain, stars and entry points."""

    lesson_selected = Signal(str)
    review_requested = Signal()

    def __init__(self, manager: LessonManager) -> None:
        super().__init__()
        self._manager = manager
        column = QVBoxLayout(self)
        column.setContentsMargins(32, 24, 32, 24)
        column.setSpacing(10)

        title = QLabel("Curso de mecanografía")
        title.setObjectName("Title")
        title.setFont(title_font())
        subtitle = QLabel("Supera una lección para desbloquear la siguiente.")
        subtitle.setObjectName("Muted")
        column.addWidget(title)
        column.addWidget(subtitle)

        self._rows_layout = QVBoxLayout()
        self._rows_layout.setSpacing(6)
        column.addLayout(self._rows_layout)
        column.addStretch(1)

        review = QPushButton("Repasar teclas débiles")
        review.clicked.connect(self.review_requested.emit)
        column.addWidget(review)

    def refresh(self, progress: dict) -> None:
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for lesson in self._manager.lessons:
            entry = progress.get(lesson.id) or {}
            unlocked = self._manager.is_unlocked(lesson, progress)
            row = LessonRow(lesson, int(entry.get("stars", 0)), unlocked)
            row.clicked.connect(self.lesson_selected.emit)
            self._rows_layout.addWidget(row)


class LessonScreen(QWidget):
    """Practice one lesson; reports the result without blocking on errors."""

    lesson_finished = Signal(str, float, float, int, dict)  # id, wpm, accuracy, stars, key_stats
    review_finished = Signal(dict)  # key_stats only; never affects lesson pass
    exit_requested = Signal()

    def __init__(self, manager: LessonManager, theme_mode: themes.ThemeMode) -> None:
        super().__init__()
        self._manager = manager
        self._lesson: Lesson | None = None
        self._review = False
        self._last_keystroke: float | None = None
        self._key_stats: dict[str, KeyStats] = {}
        self._sound_player = None
        self._build(theme_mode)

    def _build(self, theme_mode: themes.ThemeMode) -> None:
        column = QVBoxLayout(self)
        column.setContentsMargins(32, 24, 32, 24)
        column.setSpacing(12)

        top = QHBoxLayout()
        back = QPushButton("← Volver")
        back.clicked.connect(self.exit_requested.emit)
        self._heading = QLabel("Lección")
        self._heading.setObjectName("Title")
        self._heading.setFont(title_font())
        self._goal = QLabel()
        self._goal.setObjectName("Muted")
        top.addWidget(back)
        top.addSpacing(12)
        top.addWidget(self._heading)
        top.addStretch(1)
        top.addWidget(self._goal)
        column.addLayout(top)

        self._typing_area = TypingArea(theme_mode)
        self._typing_area.keyPressed.connect(self._on_char)
        self._typing_area.backspacePressed.connect(self._on_backspace)
        column.addWidget(self._typing_area, 1)

        self._keyboard = VirtualKeyboard(theme_mode=theme_mode)
        column.addWidget(self._keyboard)

        stats = QHBoxLayout()
        self._wpm = QLabel("0 WPM")
        self._wpm.setObjectName("Title")
        self._wpm.setFont(title_font())
        self._accuracy = QLabel("100 %")
        self._accuracy.setObjectName("Title")
        self._accuracy.setFont(title_font())
        self._progress = QLabel("0 %")
        self._progress.setObjectName("Muted")
        stats.addWidget(self._wpm)
        stats.addSpacing(16)
        stats.addWidget(self._accuracy)
        stats.addStretch(1)
        stats.addWidget(self._progress)
        column.addLayout(stats)

        self._feedback = QLabel()
        self._feedback.setWordWrap(True)
        self._feedback.hide()
        column.addWidget(self._feedback)

        buttons = QHBoxLayout()
        self._retry = QPushButton("Reintentar")
        self._retry.clicked.connect(self._restart)
        self._continue = QPushButton("Continuar")
        self._continue.clicked.connect(self.exit_requested.emit)
        buttons.addStretch(1)
        buttons.addWidget(self._retry)
        buttons.addWidget(self._continue)
        column.addLayout(buttons)

    def start(self, lesson: Lesson, progress: dict, layout: KeyboardLayout | None = None) -> None:
        self._lesson = lesson
        self._review = False
        self._progress_snapshot = dict(progress)
        self._layout = layout
        text = self._manager.lesson_text(lesson, progress)
        self._start_session(text, layout)
        self._goal.setText(
            f"Objetivo: {lesson.min_wpm:.0f} WPM netos y {lesson.min_accuracy:.0f} % de precisión"
        )

    def start_review(self, drill_text: str, layout: KeyboardLayout | None = None) -> None:
        self._lesson = None
        self._review = True
        self._layout = layout
        self._start_session(drill_text, layout)
        self._goal.setText("Repaso de teclas débiles; no afecta a la nota de las lecciones")

    def _start_session(self, text: str, layout: KeyboardLayout | None) -> None:
        self._text = text
        self._typed = ""
        self._start_time: float | None = None
        self._key_stats = {}
        self._last_keystroke = None
        self._layout = layout
        self._states = ["pending"] * len(text)
        self._feedback.hide()
        self._retry.hide()
        self._continue.hide()
        self._typing_area.set_keyboard_layout(layout)
        self._typing_area.load(text, self._states)
        self._typing_area.setFocus()
        if layout is not None:
            self._keyboard.set_layout(layout.name)
        self._keyboard.set_target(text[0] if text else None)
        self._refresh_labels(0.0, 100.0)

    def set_weak_keys(self, keys: dict[str, float]) -> None:
        self._keyboard.set_weak_keys(keys)

    def set_keyboard_visible(self, visible: bool) -> None:
        self._keyboard.setVisible(visible)

    def set_sound_player(self, player) -> None:
        self._sound_player = player

    def apply_effects(self, level: str, reduce_motion: bool) -> None:
        self._typing_area.set_effects_level(level, reduce_motion)

    def _restart(self) -> None:
        if self._review:
            self._start_session(self._text, self._layout)
        elif self._lesson is not None:
            self.start(self._lesson, self._progress_snapshot, self._layout)

    def _on_char(self, char: str) -> None:
        if self._start_time is None:
            self._start_time = time.perf_counter()
        position = len(self._typed)
        if position >= len(self._text):
            return
        expected = self._text[position]
        now = time.perf_counter()
        latency = 0.0 if self._last_keystroke is None else now - self._last_keystroke
        self._last_keystroke = now
        self._record_keystroke(expected, char, latency)
        if self._sound_player is not None:
            self._sound_player.play(SoundId.KEY)
            if char != expected:
                self._sound_player.play(SoundId.ERROR)
        self._typed += char
        if char == expected:
            self._states[position] = "correct"
        else:
            self._states[position] = "incorrect"
        self._typing_area.update_state(position + 1, self._states)
        next_position = len(self._typed)
        next_char = self._text[next_position] if next_position < len(self._text) else None
        self._keyboard.set_target(next_char)
        wpm, accuracy = self._metrics()
        self._refresh_labels(wpm, accuracy)
        if len(self._typed) >= len(self._text):
            self._finish()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.exit_requested.emit()
            return
        super().keyPressEvent(event)

    def _on_backspace(self) -> None:
        if not self._typed:
            return
        position = len(self._typed) - 1
        self._typed = self._typed[:-1]
        self._states[position] = "pending"
        self._typing_area.update_state(position, self._states)

    def _record_keystroke(self, expected: str, got: str, latency: float) -> None:
        stats = self._key_stats.setdefault(expected, KeyStats())
        stats.attempts += 1
        if got != expected:
            stats.errors += 1
        stats.latency_total += latency
        stats.latency_samples += 1

    def _metrics(self) -> tuple[float, float]:
        if self._start_time is None or not self._typed:
            return 0.0, 100.0
        minutes = max(time.perf_counter() - self._start_time, 0.3) / 60.0
        correct = sum(1 for s in self._states if s == "correct")
        wpm = (correct / 5.0) / minutes
        accuracy = 100.0 * correct / max(1, len(self._typed))
        return wpm, accuracy

    def _refresh_labels(self, wpm: float, accuracy: float) -> None:
        self._wpm.setText(f"{wpm:.0f} WPM")
        self._accuracy.setText(f"{accuracy:.0f} %")
        self._progress.setText(f"{100 * len(self._typed) // max(1, len(self._text))} %")

    def _finish(self) -> None:
        wpm, accuracy = self._metrics()
        key_stats = self._key_stats
        if self._review or self._lesson is None:
            self._feedback.setText(
                "Repaso terminado. Cada pulsación alimenta el mapa de teclas débiles."
            )
            self._feedback.show()
            self._continue.show()
            self.review_finished.emit(key_stats)
            return
        stars = self._manager.stars_for(self._lesson, wpm, accuracy)
        if stars >= 1:
            self._feedback.setText(
                f"Lección superada con {stars} {stars_label(stars)} "
                f"({wpm:.0f} WPM, {accuracy:.0f} % de precisión)."
            )
        else:
            self._feedback.setText(
                f"No superada: necesitas {self._lesson.min_wpm:.0f} WPM y "
                f"{self._lesson.min_accuracy:.0f} % de precisión. Reintenta cuando quieras."
            )
        self._feedback.show()
        self._retry.show()
        self._continue.show()
        self.lesson_finished.emit(self._lesson.id, wpm, accuracy, stars, key_stats)

    def set_theme(self, mode: themes.ThemeMode) -> None:
        self._typing_area.set_theme(mode)


class CoursePage(QWidget):
    """Stacked course flow: list ↔ lesson."""

    lesson_completed = Signal(str, float, float, int, dict)
    review_drill_requested = Signal()

    def __init__(self, manager: LessonManager, theme_mode: themes.ThemeMode) -> None:
        super().__init__()
        self._manager = manager
        self.stack = QStackedWidget()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.stack)

        self.list_screen = CourseListScreen(manager)
        self.lesson_screen = LessonScreen(manager, theme_mode)
        self.stack.addWidget(self.list_screen)
        self.stack.addWidget(self.lesson_screen)

        self.list_screen.lesson_selected.connect(self._open_lesson)
        self.list_screen.review_requested.connect(self.review_drill_requested.emit)
        self.lesson_screen.exit_requested.connect(self._show_list)
        self.lesson_screen.lesson_finished.connect(self.lesson_completed.emit)
        self.lesson_screen.review_finished.connect(lambda stats: self._show_list())
        self.refresh({})

    def refresh(self, progress: dict) -> None:
        self._progress = progress
        self.list_screen.refresh(progress)

    def _open_lesson(self, lesson_id: str) -> None:
        lesson = next((item for item in self._manager.lessons if item.id == lesson_id), None)
        if lesson is None:
            return
        self.lesson_screen.start(lesson, self._progress, self._current_layout())
        self.stack.setCurrentWidget(self.lesson_screen)

    def open_review(self, drill_text: str) -> None:
        self.lesson_screen.start_review(drill_text, self._current_layout())
        self.stack.setCurrentWidget(self.lesson_screen)

    def _show_list(self) -> None:
        self.refresh(self._progress)
        self.stack.setCurrentWidget(self.list_screen)

    def _current_layout(self) -> KeyboardLayout | None:
        name = self.property("layout_name")
        return load_layout(str(name)) if name else None

    def set_layout_name(self, name: str) -> None:
        self.setProperty("layout_name", name)
