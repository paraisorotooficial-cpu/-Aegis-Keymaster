"""Progress panel: trends, records, heatmaps and history table (QPainter only)."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.stats import Stats
from src.core.user_data import UserData
from src.ui import themes

HEATMAP_ROWS = (
    "1234567890",
    "qwertyuiop",
    "asdfghjklñ",
    "zxcvbnm,.",
)


class LineChart(QWidget):
    """Minimal QPainter line chart with a baseline."""

    def __init__(self, label: str) -> None:
        super().__init__()
        self._label = label
        self._values: list[float] = []
        self._theme = themes.get_theme(themes.ThemeMode.NEON)
        self.setMinimumHeight(110)

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
        pad = 10.0
        painter.setPen(QPen(QColor(self._theme.text_muted), 1))
        painter.drawText(QRectF(pad, 4, w - 2 * pad, 16), Qt.AlignmentFlag.AlignLeft, self._label)
        if len(self._values) < 2:
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Datos insuficientes")
            return
        low, high = min(self._values), max(self._values)
        span = (high - low) or 1.0
        step = (w - 2 * pad) / (len(self._values) - 1)
        points = QPolygonF()
        for i, value in enumerate(self._values):
            x = pad + i * step
            y = h - pad - ((value - low) / span) * (h - 2 * pad - 20)
            points.append(QPointF(x, y))
        painter.setPen(QPen(QColor(self._theme.cyan), 2))
        painter.drawPolyline(points)


class KeyboardHeatmap(QWidget):
    """Per-key heatmap over a simplified layout: error rate or latency."""

    def __init__(self) -> None:
        super().__init__()
        self._data: dict[str, dict[str, float]] = {}
        self._show_latency = False
        self._theme = themes.get_theme(themes.ThemeMode.NEON)
        self.setMinimumHeight(150)

    def set_theme(self, mode: themes.ThemeMode) -> None:
        self._theme = themes.get_theme(mode)
        self.update()

    def set_data(self, data: dict[str, dict[str, float]]) -> None:
        self._data = data
        self.update()

    def toggle_metric(self) -> bool:
        self._show_latency = not self._show_latency
        self.update()
        return self._show_latency

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(self._theme.bg_deep))
        w = float(self.width())
        margin, gap = 16.0, 4.0
        cell_w = (w - 2 * margin - gap * 9) / 10
        cell_h = min(34.0, (float(self.height()) - 2 * margin - 3 * gap) / 4)
        y = margin
        for row in HEATMAP_ROWS:
            offset = margin + (10 - len(row)) * (cell_w + gap) / 2
            for i, key in enumerate(row):
                x = offset + i * (cell_w + gap)
                color = self._color_for(key)
                rect = QRectF(x, y, cell_w, cell_h)
                painter.setPen(QPen(QColor(self._theme.border), 1))
                painter.setBrush(color)
                painter.drawRoundedRect(rect, 4, 4)
                painter.setPen(QPen(QColor(self._theme.text_primary), 1))
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, key)
            y += cell_h + gap

    def _color_for(self, key: str) -> QColor:
        entry = self._data.get(key)
        if not entry or not entry.get("attempts"):
            return QColor(self._theme.bg_panel)
        if self._show_latency:
            intensity = min(1.0, entry["avg_latency"] / 1.5)
            base = QColor(self._theme.cyan)
        else:
            intensity = min(1.0, entry["error_rate"] / 0.4)
            base = QColor(self._theme.amber)
        alpha = 0.25 + 0.75 * intensity
        background = QColor(self._theme.bg_panel)
        blended = QColor(
            round(background.redF() * (1 - alpha) + base.redF() * alpha),
            round(background.greenF() * (1 - alpha) + base.greenF() * alpha),
            round(background.blueF() * (1 - alpha) + base.blueF() * alpha),
        )
        return blended


class ProgressScreen(QWidget):
    """Summary, trends, records, heatmap and filterable history."""

    data_changed = Signal()

    def __init__(self, user_data: UserData) -> None:
        super().__init__()
        self._user_data = user_data
        self._stats = Stats(user_data)
        self._build()

    def _build(self) -> None:
        column = QVBoxLayout(self)
        column.setContentsMargins(32, 24, 32, 24)
        column.setSpacing(12)

        title = QLabel("Progreso")
        title.setObjectName("Title")
        column.addWidget(title)

        summary = QGridLayout()
        self._summary_labels: dict[str, QLabel] = {}
        for index, (key, label) in enumerate(
            (("streak", "Racha de días"), ("time", "Tiempo practicado"), ("tests", "Tests válidos"))
        ):
            value = QLabel("—")
            value.setObjectName("Title")
            caption = QLabel(label)
            caption.setObjectName("Subtitle")
            summary.addWidget(value, 0, index)
            summary.addWidget(caption, 1, index)
            self._summary_labels[key] = value
        column.addLayout(summary)

        charts = QHBoxLayout()
        self._wpm_chart = LineChart("WPM neto (media móvil)")
        self._accuracy_chart = LineChart("Precisión (media móvil)")
        charts.addWidget(self._wpm_chart, 1)
        charts.addWidget(self._accuracy_chart, 1)
        column.addLayout(charts, 2)

        heat_row = QHBoxLayout()
        heat_title = QLabel("Mapa de calor del teclado")
        heat_title.setObjectName("Secondary")
        self._heat_toggle = QPushButton("Ver latencia")
        self._heat_toggle.clicked.connect(self._on_toggle_heat)
        heat_row.addWidget(heat_title)
        heat_row.addStretch(1)
        heat_row.addWidget(self._heat_toggle)
        column.addLayout(heat_row)
        self._heatmap = KeyboardHeatmap()
        column.addWidget(self._heatmap, 2)

        filters = QHBoxLayout()
        filters.addWidget(QLabel("Modo:"))
        self._mode_filter = QComboBox()
        self._mode_filter.addItem("Todos", None)
        self._mode_filter.addItem("Test", "test")
        self._mode_filter.addItem("Lección", "lesson")
        filters.addWidget(self._mode_filter)
        filters.addWidget(QLabel("Duración:"))
        self._duration_filter = QComboBox()
        self._duration_filter.addItem("Todas", None)
        for duration in (60, 180, 300):
            self._duration_filter.addItem(f"{duration // 60} min", duration)
        filters.addWidget(self._duration_filter)
        filters.addStretch(1)
        self._mode_filter.currentIndexChanged.connect(lambda _: self._refresh_table())
        self._duration_filter.currentIndexChanged.connect(lambda _: self._refresh_table())
        column.addLayout(filters)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(
            ["Fecha", "Modo", "Duración", "WPM neto", "Precisión"]
        )
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        column.addWidget(self._table, 3)

    # -- refresh ---------------------------------------------------

    def refresh(self) -> None:
        stats = self._stats
        self._summary_labels["streak"].setText(f"{stats.day_streak()} d")
        minutes = stats.total_practice_seconds() / 60.0
        self._summary_labels["time"].setText(f"{minutes:.0f} min")
        self._summary_labels["tests"].setText(str(stats.total_tests()))
        self._wpm_chart.set_values(stats.wpm_trend())
        self._accuracy_chart.set_values(stats.accuracy_trend())
        self._heatmap.set_data(stats.heatmap())
        self._refresh_table()

    def _refresh_table(self) -> None:
        rows = self._stats.filter_history(
            mode=self._mode_filter.currentData(),
            duration=self._duration_filter.currentData(),
        )
        rows = list(reversed(rows))[:100]
        self._table.setRowCount(len(rows))
        for r, entry in enumerate(rows):
            values = (
                str(entry.get("timestamp", ""))[:16].replace("T", " "),
                str(entry.get("mode", "test")),
                f"{int(entry.get('duration_seconds', 0)) // 60} min",
                f"{float(entry.get('net_wpm', 0)):.1f}",
                f"{float(entry.get('accuracy', 0)):.1f} %",
            )
            for c, text in enumerate(values):
                self._table.setItem(r, c, QTableWidgetItem(text))

    def _on_toggle_heat(self) -> None:
        showing_latency = self._heatmap.toggle_metric()
        self._heat_toggle.setText("Ver errores" if showing_latency else "Ver latencia")

    def set_theme(self, mode: themes.ThemeMode) -> None:
        self._wpm_chart.set_theme(mode)
        self._accuracy_chart.set_theme(mode)
        self._heatmap.set_theme(mode)

    def attach(self, user_data: UserData) -> None:
        self._user_data = user_data
        self._stats = Stats(user_data)
        self.refresh()
