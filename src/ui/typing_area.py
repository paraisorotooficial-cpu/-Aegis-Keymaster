"""Typing area painted with QPainter — the heart of the app.

The only neon-glowing element in the product. Text layout is computed once
per (text, font, width) and cached; keystrokes only repaint the affected
line. Pending text is dim, correct text is primary, incorrect is red with
underline (never color alone).
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from src.core.layouts import KeyboardLayout
from src.ui import themes

LINE_MAX_CHARS = 80
CURSOR_ANIMATION_MS = 90


class TypingArea(QWidget):
    """Displays target text with per-char state and an animated cursor."""

    keyPressed = Signal(str)  # the character typed
    backspacePressed = Signal()

    def __init__(self, theme_mode: themes.ThemeMode = themes.ThemeMode.NEON) -> None:
        super().__init__()
        self._theme = themes.get_theme(theme_mode)
        self._text = ""
        self._states: list[str] = []
        self._position = 0
        self._font = QFont("JetBrains Mono", 16)
        self._font.setStyleHint(QFont.StyleHint.Monospace)
        self._metrics: QFontMetricsF | None = None
        self._lines: list[tuple[int, int]] = []  # (start, end) index per visual line
        self._layout: KeyboardLayout | None = None
        self._pending_dead: str | None = None
        self.setMinimumHeight(120)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.IBeamCursor)

    # -- public API ------------------------------------------------

    def set_theme(self, mode: themes.ThemeMode) -> None:
        self._theme = themes.get_theme(mode)
        self.update()

    def set_keyboard_layout(self, layout: KeyboardLayout | None) -> None:
        """Enable dead-key composition when a layout is provided."""
        self._layout = layout
        self._pending_dead = None

    def load(self, text: str, states: list[str] | None = None) -> None:
        self._text = text
        self._states = states if states is not None else ["pending"] * len(text)
        self._position = 0
        self._relayout()
        self.update()

    def update_state(self, position: int, states: list[str]) -> None:
        self._position = position
        self._states = states
        self.update()

    # -- events ----------------------------------------------------

    def keyPressEvent(self, event) -> None:
        text = event.text()
        if event.key() == Qt.Key.Key_Backspace:
            if self._pending_dead:
                self._pending_dead = None
            else:
                self.backspacePressed.emit()
            event.accept()
            return
        if not text or not text.isprintable():
            event.ignore()
            return
        char = self._compose_dead_keys(text)
        if char is not None:
            self.keyPressed.emit(char)
        event.accept()

    def _compose_dead_keys(self, text: str) -> str | None:
        """Hold dead keys and compose them; None means 'swallow this press'."""
        if self._layout is None:
            return text
        spec = self._layout.spec(text)
        if spec is not None and spec.dead:
            self._pending_dead = text
            self.update()
            return None
        if self._pending_dead is None:
            return text
        dead = self._pending_dead
        self._pending_dead = None
        if text == " ":
            return dead
        return self._layout.compose(dead, text) or text

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.fillRect(self.rect(), QColor(self._theme.bg_deep))

        if not self._text or self._metrics is None:
            return

        metrics = self._metrics
        line_height = metrics.height() * 1.5
        char_width = metrics.horizontalAdvance("M")
        margin = 24.0
        y = margin

        for start, end in self._lines:
            x = margin
            for i in range(start, end):
                state = self._states[i] if i < len(self._states) else "pending"
                char = self._text[i]
                color = self._color_for(state)
                painter.setPen(QPen(color))
                painter.drawText(QPointF(x, y + metrics.ascent()), char)

                if state == "incorrect":
                    pen = QPen(QColor(self._theme.error), 2)
                    painter.setPen(pen)
                    underline_y = y + metrics.ascent() + 3
                    painter.drawLine(QPointF(x, underline_y), QPointF(x + char_width, underline_y))

                if i == self._position:
                    self._draw_cursor(painter, x, y, metrics, line_height)

                x += metrics.horizontalAdvance(char)
            y += line_height
            if y > self.height():
                break

    # -- internals -------------------------------------------------

    def _color_for(self, state: str) -> QColor:
        if state == "correct":
            return QColor(self._theme.text_primary)
        if state == "incorrect":
            return QColor(self._theme.error)
        return QColor(self._theme.text_muted)

    def _draw_cursor(self, painter: QPainter, x: float, y: float,
                     metrics: QFontMetricsF, line_height: float) -> None:
        cursor_color = QColor(self._theme.cyan)
        path = QPainterPath()
        rect = QRectF(x - 1, y + 2, 2.5, metrics.height())
        path.addRect(rect)
        painter.fillPath(path, cursor_color)
        glow = QColor(self._theme.cyan_glow)
        glow.setAlpha(70)
        halo = QRectF(x - 4, y - 1, 8.5, metrics.height() + 6)
        painter.fillRect(halo, glow)

    def _relayout(self) -> None:
        self._metrics = QFontMetricsF(self._font)
        width = max(1.0, self.width() - 48.0)
        metrics = self._metrics
        lines: list[tuple[int, int]] = []
        start = 0
        line_width = 0.0
        for i, char in enumerate(self._text):
            line_width += metrics.horizontalAdvance(char)
            if line_width > width or (i - start >= LINE_MAX_CHARS and char == " "):
                lines.append((start, i))
                start = i
                line_width = 0.0
        lines.append((start, len(self._text)))
        self._lines = lines
        needed = int(24 + len(lines) * metrics.height() * 1.5 + 24)
        self.setMinimumHeight(min(needed, 320))
