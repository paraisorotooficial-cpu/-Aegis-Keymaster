"""Main window shell with navigation and theme switching."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.ui import themes
from src.ui.test_mode import TestPage

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
        self.stack.addWidget(TestPage())
        self.stack.addWidget(self._placeholder("Progreso", "Tu evolución aparecerá aquí."))
        self.stack.addWidget(self._placeholder("Ajustes", "Configura tema, sonido y teclado."))
        layout.addWidget(self.stack, 1)

        self._nav_buttons: list[QPushButton] = []
        self._build_nav_buttons()

        self.setCentralWidget(central)

    def _build_top_bar(self, theme_mode: themes.ThemeMode) -> QFrame:
        bar = QFrame()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(52)
        self._bar_row = QHBoxLayout(bar)
        self._bar_row.setContentsMargins(20, 0, 20, 0)

        brand = QLabel("AEGIS KEYMASTER")
        brand.setObjectName("Title")
        self._bar_row.addWidget(brand)
        self._bar_row.addSpacing(24)

        self.theme_selector = QComboBox()
        for mode in themes.ThemeMode:
            self.theme_selector.addItem(mode.value.capitalize(), mode.value)
        self.theme_selector.setCurrentIndex(list(themes.ThemeMode).index(theme_mode))
        self.theme_selector.currentIndexChanged.connect(self._on_theme_selected)
        self._bar_row.addStretch(1)
        self._bar_row.addWidget(self.theme_selector)
        return bar

    def _build_nav_buttons(self) -> None:
        for index, name in enumerate(NAV_ITEMS):
            button = QPushButton(name)
            button.setFlat(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _=False, i=index: self.navigate(i))
            self._bar_row.insertWidget(2 + index, button)
            self._nav_buttons.append(button)
        self._nav_buttons[0].setDefault(True)

    def navigate(self, index: int) -> None:
        if 0 <= index < self.stack.count():
            self.stack.setCurrentIndex(index)

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
