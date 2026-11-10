"""Timed test mode UI: setup, live test and report screens."""

from __future__ import annotations

from PySide6.QtCore import QPointF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.core.sound import SoundId
from src.core.test_texts import TestTextBank
from src.core.typing_test import (
    ALLOWED_DURATIONS,
    TestResult,
    TypingTestSession,
)
from src.ui import themes
from src.ui.fonts import subtitle_font, title_font
from src.ui.typing_area import TypingArea
from src.ui.virtual_keyboard import VirtualKeyboard

LANGUAGE_NAMES = {"es": "Español", "en": "English"}


def format_duration(seconds: int) -> str:
    minutes = seconds // 60
    return f"{minutes} min"


class IntervalChart(QWidget):
    """Lightweight QPainter line chart of WPM per 5-second interval."""

    def __init__(self) -> None:
        super().__init__()
        self._values: list[float] = []
        self._theme = themes.get_theme(themes.ThemeMode.NEON)
        self.setMinimumHeight(120)

    def set_theme(self, mode: themes.ThemeMode) -> None:
        self._theme = themes.get_theme(mode)
        self.update()

    def set_values(self, values: list[float]) -> None:
        self._values = values
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(self._theme.bg_panel))
        w, h = float(self.width()), float(self.height())
        pad = 12.0
        painter.setPen(QPen(QColor(self._theme.border), 1))
        painter.drawLine(QPointF(pad, h / 2), QPointF(w - pad, h / 2))

        if not self._values:
            painter.setPen(QPen(QColor(self._theme.text_muted), 1))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Sin datos")
            return

        peak = max(self._values) or 1.0
        step = (w - 2 * pad) / max(1, len(self._values) - 1)
        points = QPolygonF()
        for i, value in enumerate(self._values):
            x = pad + i * step
            y = h - pad - (value / peak) * (h - 2 * pad)
            points.append(QPointF(x, y))
        painter.setPen(QPen(QColor(self._theme.cyan), 2))
        painter.drawPolyline(points)
        painter.setPen(QPen(QColor(self._theme.cyan_glow), 6))
        painter.drawPoint(points.last())


class TestSetupScreen(QWidget):
    """Choose duration, language and start."""

    start_requested = Signal(int, str)

    def __init__(self) -> None:
        super().__init__()
        self._build()

    def _build(self) -> None:
        column = QVBoxLayout(self)
        column.addStretch(1)

        title = QLabel("Test cronometrado")
        title.setObjectName("Title")
        title.setFont(title_font())
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        subtitle = QLabel("Elige la duración y mide tu velocidad real.")
        subtitle.setObjectName("Subtitle")
        subtitle.setFont(subtitle_font())
        subtitle.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        column.addWidget(title)
        column.addWidget(subtitle)
        column.addSpacing(24)

        row = QHBoxLayout()
        row.addStretch(1)
        self._duration_buttons: dict[int, QPushButton] = {}
        for duration in ALLOWED_DURATIONS:
            button = QPushButton(format_duration(duration))
            button.setCheckable(True)
            button.clicked.connect(lambda _=False, d=duration: self._select_duration(d))
            self._duration_buttons[duration] = button
            row.addWidget(button)
        row.addStretch(1)
        column.addLayout(row)

        lang_row = QHBoxLayout()
        lang_row.addStretch(1)
        lang_label = QLabel("Idioma del texto:")
        lang_label.setObjectName("Secondary")
        self._language = QComboBox()
        for code, name in LANGUAGE_NAMES.items():
            self._language.addItem(name, code)
        lang_row.addWidget(lang_label)
        lang_row.addWidget(self._language)
        lang_row.addStretch(1)
        column.addLayout(lang_row)

        start_row = QHBoxLayout()
        start_row.addStretch(1)
        self._start_button = QPushButton("Empezar test")
        self._start_button.setObjectName("Primary")
        self._start_button.clicked.connect(self._emit_start)
        start_row.addWidget(self._start_button)
        start_row.addStretch(1)
        column.addLayout(start_row)
        column.addStretch(1)

        self._select_duration(60)

    def _select_duration(self, duration: int) -> None:
        self._selected_duration = duration
        for value, button in self._duration_buttons.items():
            button.setChecked(value == duration)

    def _emit_start(self) -> None:
        self.start_requested.emit(self._selected_duration, self._language.currentData())


class TestLiveScreen(QWidget):
    """Live test: countdown, live WPM, accuracy and the typing area."""

    finished = Signal(object, dict)  # TestResult, key_stats

    def __init__(self, text_bank: TestTextBank | None = None) -> None:
        super().__init__()
        self._text_bank = text_bank or TestTextBank()
        self._session: TypingTestSession | None = None
        self._sound_player = None
        self._theme_mode = themes.ThemeMode.NEON
        self._build()
        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._on_tick)

    def _build(self) -> None:
        column = QVBoxLayout(self)
        column.setContentsMargins(24, 16, 24, 16)

        top = QHBoxLayout()
        self._duration_label = QLabel()
        self._duration_label.setObjectName("Secondary")
        self._countdown = QLabel()
        self._countdown.setObjectName("AccentCyan")
        self._live_wpm = QLabel("0 WPM")
        self._live_wpm.setObjectName("Title")
        self._live_wpm.setFont(title_font())
        self._live_accuracy = QLabel("100 %")
        self._live_accuracy.setObjectName("Secondary")
        top.addWidget(self._duration_label)
        top.addStretch(1)
        top.addWidget(self._countdown)
        top.addStretch(1)
        top.addWidget(self._live_wpm)
        top.addSpacing(16)
        top.addWidget(self._live_accuracy)
        column.addLayout(top)

        self._typing_area = TypingArea(self._theme_mode)
        self._typing_area.keyPressed.connect(self._on_char)
        self._typing_area.backspacePressed.connect(self._on_backspace)
        column.addWidget(self._typing_area, 1)

        self._keyboard = VirtualKeyboard(theme_mode=self._theme_mode)
        column.addWidget(self._keyboard)

        bottom = QHBoxLayout()
        self._hint = QLabel("Empieza a escribir para arrancar el cronómetro.")
        self._hint.setObjectName("Muted")
        abort = QPushButton("Abandonar")
        abort.clicked.connect(self._on_abort)
        bottom.addWidget(self._hint)
        bottom.addStretch(1)
        bottom.addWidget(abort)
        column.addLayout(bottom)

    def start(self, duration: int, language: str) -> None:
        text = self._text_bank.pick(language, duration)
        self._session = TypingTestSession(text, duration)
        self._duration_label.setText(
            f"Test {format_duration(duration)} · {LANGUAGE_NAMES[language]}"
        )
        self._countdown.setText(self._format_remaining(duration))
        self._live_wpm.setText("0 WPM")
        self._live_accuracy.setText("100 %")
        self._typing_area.load(text, self._session.states)
        self._typing_area.setFocus()
        self._keyboard.set_target(text[0] if text else None)
        self._timer.start()

    def set_layout_name(self, name: str) -> None:
        self._keyboard.set_layout(name)

    def set_sound_player(self, player) -> None:
        self._sound_player = player

    def set_keyboard_visible(self, visible: bool) -> None:
        self._keyboard.setVisible(visible)

    def apply_effects(self, level: str, reduce_motion: bool) -> None:
        self._typing_area.set_effects_level(level, reduce_motion)

    @staticmethod
    def _format_remaining(seconds: float) -> str:
        seconds = max(0, round(seconds))
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def _on_char(self, char: str) -> None:
        if self._session is None:
            return
        position = self._session.position
        expected = self._session.text[position] if position < len(self._session.text) else None
        self._session.type_char(char)
        if self._sound_player is not None:
            self._sound_player.play(SoundId.KEY)
            if expected is not None and char != expected:
                self._sound_player.play(SoundId.ERROR)
        if self._session.position >= len(self._session.text) - 40:
            extra = self._text_bank.pick("es", 60) + " " + self._text_bank.pick("en", 60)
            self._session.extend(extra)
            self._typing_area.load(self._session.text, self._session.states)
            self._typing_area.update_state(self._session.position, self._session.states)
        self._refresh()
        if self._session.finished:
            self._stop()

    def _on_backspace(self) -> None:
        if self._session is not None:
            self._session.backspace()
            self._refresh()

    def _on_tick(self) -> None:
        if self._session is not None and self._session.tick():
            self._refresh()
            self._stop()

    def _refresh(self) -> None:
        if self._session is None:
            return
        self._countdown.setText(self._format_remaining(self._session.remaining))
        self._live_wpm.setText(f"{self._session.live_wpm():.0f} WPM")
        result = self._session.result()
        if result.total_keystrokes:
            self._live_accuracy.setText(f"{result.accuracy:.0f} %")
        self._typing_area.update_state(self._session.position, self._session.states)
        position = self._session.position
        self._keyboard.set_target(
            self._session.text[position] if position < len(self._session.text) else None
        )

    def _on_abort(self) -> None:
        if self._session is not None and not self._session.finished:
            self._stop(aborted=True)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self._on_abort()
            return
        super().keyPressEvent(event)

    def _stop(self, aborted: bool = False) -> None:
        self._timer.stop()
        assert self._session is not None
        result = self._session.abort() if aborted else self._session.result()
        self.finished.emit(result, self._session.key_stats())

    def set_theme(self, mode: themes.ThemeMode) -> None:
        self._theme_mode = mode
        self._typing_area.set_theme(mode)


class TestReportScreen(QWidget):
    """Post-test report: metrics, chart, weak keys and actions."""

    repeat_requested = Signal()
    review_requested = Signal(dict)  # key_stats dict[str, KeyAttempt]

    def __init__(self) -> None:
        super().__init__()
        self._best: dict[int, TestResult] = {}
        self._build()

    def _build(self) -> None:
        column = QVBoxLayout(self)
        column.setContentsMargins(32, 24, 32, 24)
        column.setSpacing(12)

        self._heading = QLabel("Resultado del test")
        self._heading.setObjectName("Title")
        self._heading.setFont(title_font())
        column.addWidget(self._heading)

        self._warning = QLabel()
        self._warning.setObjectName("Muted")
        self._warning.setWordWrap(True)
        self._warning.hide()
        column.addWidget(self._warning)

        grid = QGridLayout()
        self._metrics: dict[str, QLabel] = {}
        for index, name in enumerate(("net_wpm", "accuracy", "consistency", "vs_best")):
            value = QLabel("—")
            value.setObjectName("Title")
            value.setFont(title_font())
            label = QLabel(
                {"net_wpm": "WPM neto", "accuracy": "Precisión",
                 "consistency": "Consistencia", "vs_best": "vs. mejor marca"}[name]
            )
            label.setObjectName("Subtitle")
            label.setFont(subtitle_font())
            grid.addWidget(value, 0, index)
            grid.addWidget(label, 1, index)
            self._metrics[name] = value
        column.addLayout(grid)

        self._chart = IntervalChart()
        column.addWidget(self._chart, 1)

        self._details = QLabel()
        self._details.setObjectName("Secondary")
        self._details.setWordWrap(True)
        column.addWidget(self._details)

        buttons = QHBoxLayout()
        review = QPushButton("Repasar teclas débiles")
        review.clicked.connect(self._emit_review)
        repeat = QPushButton("Repetir test")
        repeat.clicked.connect(self.repeat_requested.emit)
        buttons.addWidget(review)
        buttons.addWidget(repeat)
        buttons.addStretch(1)
        column.addLayout(buttons)

    def show_result(self, result: TestResult, duration: int, language: str) -> None:
        self._heading.setText(
            f"Resultado del test · {format_duration(duration)} · {LANGUAGE_NAMES[language]}"
        )

        if not result.valid:
            self._warning.setText(
                "Test no válido: dura menos de 5 segundos o tiene menos de 10 pulsaciones. "
                "No se guarda en el historial ni cuenta para récords."
            )
            self._warning.show()
        else:
            self._warning.hide()

        self._metrics["net_wpm"].setText(f"{result.net_wpm:.1f}")
        self._metrics["accuracy"].setText(f"{result.accuracy:.1f} %")
        self._metrics["consistency"].setText(f"{result.consistency:.0f} %")
        self._chart.set_values([i.wpm for i in result.intervals])

        best = self._best.get(duration)
        if best is not None and result.valid:
            delta = result.net_wpm - best.net_wpm
            sign = "+" if delta >= 0 else ""
            self._metrics["vs_best"].setText(f"{sign}{delta:.1f}")
        else:
            self._metrics["vs_best"].setText("—")

        if result.valid and (best is None or result.net_wpm > best.net_wpm):
            self._best[duration] = result

        self._details.setText(
            f"WPM bruto {result.gross_wpm:.1f}"
            f" · errores sin corregir {result.uncorrected_errors}"
            f" · pulsaciones {result.total_keystrokes}"
        )

    def attach_key_stats(self, key_stats: dict) -> None:
        """Store the session's per-key stats for the review action."""
        self._last_key_stats = key_stats
        weak = sorted(
            ((key, s.error_rate) for key, s in key_stats.items() if s.errors > 0),
            key=lambda item: -item[1],
        )[:5]
        if weak:
            text = "Teclas débiles del test: " + ", ".join(
                f"{key} ({rate * 100:.0f} %)" for key, rate in weak
            )
        else:
            text = "Sin teclas débiles en este test: excelente precisión."
        self._details.setText(self._details.text() + " · " + text)

    def _emit_review(self) -> None:
        self.review_requested.emit(self._last_key_stats or {})

    def set_theme(self, mode: themes.ThemeMode) -> None:
        self._chart.set_theme(mode)


class TestPage(QWidget):
    """Controller widget: setup → live → report flow."""

    test_completed = Signal(object, dict)  # TestResult, key_stats

    def __init__(self) -> None:
        super().__init__()
        self._duration = 60
        self._language = "es"
        self._theme_mode = themes.ThemeMode.NEON

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._stack = QStackedWidget()
        self._setup = TestSetupScreen()
        self._live = TestLiveScreen()
        self._report = TestReportScreen()
        self._stack.addWidget(self._setup)
        self._stack.addWidget(self._live)
        self._stack.addWidget(self._report)
        layout.addWidget(self._stack)

        self._setup.start_requested.connect(self._on_start)
        self._live.finished.connect(self._on_finished)
        self._report.repeat_requested.connect(self._on_repeat)
        self._report.review_requested.connect(self._on_review)

    def _on_start(self, duration: int, language: str) -> None:
        self._duration = duration
        self._language = language
        self._live.start(duration, language)
        self._stack.setCurrentWidget(self._live)

    def set_layout_name(self, name: str) -> None:
        self._live.set_layout_name(name)

    def set_sound_player(self, player) -> None:
        self._live.set_sound_player(player)

    def apply_effects(self, level: str, reduce_motion: bool) -> None:
        self._live.apply_effects(level, reduce_motion)

    def set_keyboard_visible(self, visible: bool) -> None:
        self._live.set_keyboard_visible(visible)

    def _on_finished(self, result, key_stats) -> None:
        self._report.show_result(result, self._duration, self._language)
        self._report.attach_key_stats(key_stats)
        self._stack.setCurrentWidget(self._report)
        self.test_completed.emit(result, key_stats)

    def _on_repeat(self) -> None:
        self._live.start(self._duration, self._language)
        self._stack.setCurrentWidget(self._live)

    def _on_review(self, key_stats: dict) -> None:
        from src.core.weak_keys import WeakKeyTracker

        tracker = WeakKeyTracker()
        for key, stats in key_stats.items():
            for _ in range(stats.attempts - stats.errors):
                tracker.record_attempt(key, key)
            for _ in range(stats.errors):
                tracker.record_attempt(key, "?")
        self._review_drill = tracker.generate_drill()
        self._stack.setCurrentWidget(self._setup)

    def current_drill(self) -> str | None:
        return getattr(self, "_review_drill", None)

    def set_theme(self, mode: themes.ThemeMode) -> None:
        self._theme_mode = mode
        self._live.set_theme(mode)
        self._report.set_theme(mode)
