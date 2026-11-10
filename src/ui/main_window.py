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

from src.core import i18n
from src.core.lessons import LessonManager
from src.core.user_data import UserData
from src.ui import themes
from src.ui.course_mode import CoursePage
from src.ui.fonts import title_font
from src.ui.progress_screen import ProgressScreen
from src.ui.settings_screen import SettingsScreen
from src.ui.test_mode import TestPage

NAV_KEYS = ("nav.course", "nav.test", "nav.progress", "nav.settings")


class MainWindow(QMainWindow):
    """Top-level window: navigation bar + stacked content area."""

    theme_changed = Signal(str)

    def __init__(
        self,
        theme_mode: themes.ThemeMode = themes.ThemeMode.NEON,
        user_data: UserData | None = None,
        lesson_manager: LessonManager | None = None,
    ) -> None:
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
        self.course_page = CoursePage(lesson_manager or LessonManager(), theme_mode)
        self.stack.addWidget(self.course_page)
        self.test_page = TestPage()
        self.stack.addWidget(self.test_page)
        self.progress_screen = ProgressScreen(user_data or UserData())
        self.stack.addWidget(self.progress_screen)
        self.settings_screen = SettingsScreen(user_data or UserData())
        self.stack.addWidget(self.settings_screen)
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
        brand.setFont(title_font())
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
        for index, key in enumerate(NAV_KEYS):
            button = QPushButton(i18n.tr(key))
            button.setFlat(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _=False, i=index: self.navigate(i))
            self._bar_row.insertWidget(2 + index, button)
            self._nav_buttons.append(button)
        self._nav_buttons[0].setDefault(True)

    def navigate(self, index: int) -> None:
        if 0 <= index < self.stack.count():
            if self.stack.widget(index) is self.progress_screen:
                self.progress_screen.refresh()
            self.stack.setCurrentIndex(index)

    def set_layout_name(self, name: str) -> None:
        self.course_page.set_layout_name(name)
        self.test_page.set_layout_name(name)

    def set_keyboard_visible(self, visible: bool) -> None:
        self.course_page.lesson_screen.set_keyboard_visible(visible)
        self.test_page.set_keyboard_visible(visible)

    def set_sound_player(self, player) -> None:
        self.test_page.set_sound_player(player)
        self.course_page.lesson_screen.set_sound_player(player)

    def apply_effects(self, controller) -> None:
        level = controller.level
        reduce_motion = getattr(controller, "_reduce_motion", False)
        controller.level_changed.connect(self._on_effects_level_changed)
        self.test_page.apply_effects(level, reduce_motion)
        self.course_page.lesson_screen.apply_effects(level, reduce_motion)

    def _on_effects_level_changed(self, level: str) -> None:
        self.test_page.apply_effects(level, False)
        self.course_page.lesson_screen.apply_effects(level, False)

    def retranslate(self) -> None:
        for index, key in enumerate(("nav.course", "nav.test", "nav.progress", "nav.settings")):
            if index < len(self._nav_buttons):
                self._nav_buttons[index].setText(i18n.tr(key))

    def _on_theme_selected(self, index: int) -> None:
        self.theme_changed.emit(self.theme_selector.itemData(index))
