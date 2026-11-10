"""Main window shell with navigation placeholders and theme switching."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.ui import themes

NAV_ITEMS = ("Curso", "Test", "Progreso", "Ajustes")


class MainWindow(QMainWindow):
    """Top-level window: navigation bar + stacked content area."""

    theme_changed = Signal(str)

    def __init__(self, theme_mode: themes.ThemeMode = themes.ThemeMode.NEON) -> None:
        super().__init__()
        self.setWindowTitle("Aegis Keymaster")
        self.resize(1100, 720)
        self.setMinimumSize(760, 520)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_top_bar(theme_mode))

        self.stack = QStackedWidget()
        self.stack.addWidget(self._placeholder("Curso", "Elige una lección para empezar."))
        self.stack.addWidget(self._placeholder("Test", "Mide tu velocidad con un test."))
        self.stack.addWidget(self._placeholder("Progreso", "Tu evolución aparecerá aquí."))
        self.stack.addWidget(self._placeholder("Ajustes", "Configura tema, sonido y teclado."))
        layout.addWidget(self.stack, 1)

        self.setCentralWidget(central)

    def _build_top_bar(self, theme_mode: themes.ThemeMode) -> QFrame:
        bar = QFrame()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(52)
        row = QHBoxLayout(bar)
        row.setContentsMargins(20, 0, 20, 0)

        brand = QLabel("AEGIS KEYMASTER")
        brand.setObjectName("Title")
        row.addWidget(brand)
        row.addSpacing(24)

        for name in NAV_ITEMS:
            label = QLabel(name)
            label.setObjectName("Secondary")
            row.addWidget(label)
            row.addSpacing(18)

        row.addStretch(1)

        self.theme_selector = QComboBox()
        for mode in themes.ThemeMode:
            self.theme_selector.addItem(mode.value.capitalize(), mode.value)
        self.theme_selector.setCurrentIndex(list(themes.ThemeMode).index(theme_mode))
        self.theme_selector.currentIndexChanged.connect(self._on_theme_selected)
        row.addWidget(self.theme_selector)
        return bar

    def _on_theme_selected(self, index: int) -> None:
        self.theme_changed.emit(self.theme_selector.itemData(index))

    def _placeholder(self, title: str, hint: str) -> QWidget:
        page = QWidget()
        column = QVBoxLayout(page)
        column.addStretch(1)
        heading = QLabel(title)
        heading.setObjectName("Title")
        heading.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        hint_label = QLabel(hint)
        hint_label.setObjectName("Muted")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        column.addWidget(heading)
        column.addWidget(hint_label)
        column.addStretch(1)
        return page
