"""Virtual keyboard drawn from layout data — never hardcoded key rows."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from src.core.layouts import KeyboardLayout, load_layout
from src.ui import themes

ROW_GAP = 6.0
KEY_GAP = 4.0


class VirtualKeyboard(QWidget):
    """Renders the active layout; highlights the next key, modifiers and weak keys."""

    def __init__(
        self,
        layout_name: str = "es",
        theme_mode: themes.ThemeMode = themes.ThemeMode.NEON,
    ) -> None:
        super().__init__()
        self._theme = themes.get_theme(theme_mode)
        self._layout: KeyboardLayout = load_layout(layout_name)
        self._target: str | None = None
        self._weak_keys: dict[str, float] = {}
        self._modifier_flag = ""  # "", "shift", "altgr", "dead"
        self.setMinimumHeight(170)

    # -- public API ------------------------------------------------

    def set_theme(self, mode: themes.ThemeMode) -> None:
        self._theme = themes.get_theme(mode)
        self.update()

    def set_layout(self, layout_name: str) -> None:
        self._layout = load_layout(layout_name)
        self.update()

    def set_target(self, char: str | None) -> None:
        self._target = char
        self._modifier_flag = ""
        if char:
            placement = self._layout.placement(char)
            if placement is None:
                if self._layout.composition(char):
                    self._modifier_flag = "dead"
            elif placement.needs_altgr:
                self._modifier_flag = "altgr"
            elif placement.needs_shift:
                self._modifier_flag = "shift"
        self.update()

    def set_weak_keys(self, keys: dict[str, float]) -> None:
        self._weak_keys = dict(keys)
        self.update()

    # -- painting --------------------------------------------------

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(self._theme.bg_deep))

        rows: dict[int, list[str]] = {}
        for char, spec in self._layout.keys.items():
            if char == " ":
                continue
            rows.setdefault(spec.row, []).append(char)

        cell = self._cell_width(rows)
        base_size = max(8.0, self.height() / 26.0)
        self._base_font_size = base_size
        font = QFont(self.font())
        font.setPointSizeF(base_size)
        painter.setFont(font)
        y = 12.0
        key_height = (self.height() - 24 - 4 * ROW_GAP) / 5
        for row_index in sorted(rows):
            x = 12.0
            for char in rows[row_index]:
                rect = QRectF(x, y, cell, key_height)
                self._draw_key(painter, rect, char)
                x += cell + KEY_GAP
            y += key_height + ROW_GAP

        space_rect = QRectF(12.0 + 4 * (cell + KEY_GAP), y, 6 * cell + 5 * KEY_GAP, key_height)
        self._draw_key(painter, space_rect, " ")
        self._draw_modifier_hints(painter, space_rect)

    def _cell_width(self, rows: dict[int, list[str]]) -> float:
        longest = max(len(row) for row in rows.values())
        available = self.width() - 24
        return (available - (longest - 1) * KEY_GAP) / longest

    def _draw_key(self, painter: QPainter, rect: QRectF, char: str) -> None:
        spec = self._layout.spec(char)
        is_target = bool(
            self._target
            and (char == self._target or (spec and spec.shift == self._target)
                 or (spec and spec.altgr == self._target))
        )
        composition = self._layout.composition(self._target) if self._target else None
        is_dead_target = composition is not None and composition[0] == char
        is_weak = char in self._weak_keys or (spec and spec.shift in self._weak_keys)

        if is_target or is_dead_target:
            fill = QColor(self._theme.cyan)
            border = QColor(self._theme.cyan)
            text_color = QColor(self._theme.bg_deep)
        else:
            fill = QColor(self._theme.bg_panel)
            border = QColor(self._theme.warning) if is_weak else QColor(self._theme.border)
            text_color = QColor(
                self._theme.text_muted if spec and spec.dead else self._theme.text_primary
            )

        path = QPainterPath()
        path.addRoundedRect(rect, 4, 4)
        painter.fillPath(path, fill)
        painter.setPen(QPen(border, 1.4 if (is_target or is_dead_target or is_weak) else 1))
        painter.drawPath(path)

        label = char if char != " " else ""
        if spec and spec.dead:
            label = f"{char} ◌"
        painter.setPen(QPen(text_color))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, label)

        if spec and spec.shift and spec.shift != char and char != " " and not is_target:
            small = QFont(self.font())
            small.setPointSizeF(max(6.0, self._base_font_size * 0.55))
            painter.setFont(small)
            painter.setPen(QPen(QColor(self._theme.text_muted)))
            top_rect = rect.adjusted(2, 1, -2, -rect.height() * 0.55)
            painter.drawText(top_rect, Qt.AlignmentFlag.AlignLeft, spec.shift)
            painter.setFont(QFont(self.font()))

    def _draw_modifier_hints(self, painter: QPainter, space_rect: QRectF) -> None:
        """Highlight Shift / AltGr / dead-key state next to the space bar."""
        labels = {
            "shift": "⇧ Shift",
            "altgr": "AltGr",
            "dead": "◌ tecla muerta",
        }
        label = labels.get(self._modifier_flag)
        if not label:
            return
        hint_rect = QRectF(
            space_rect.right() + KEY_GAP * 2, space_rect.top(), 110, space_rect.height()
        )
        painter.setPen(QPen(QColor(self._theme.cyan)))
        painter.drawText(hint_rect, Qt.AlignmentFlag.AlignVCenter, label)
        painter.setPen(QPen(QColor(self._theme.cyan_glow), 4))
        painter.drawPoint(QPointF(hint_rect.left() - 4, space_rect.center().y()))
