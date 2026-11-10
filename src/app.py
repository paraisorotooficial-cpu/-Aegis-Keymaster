"""Application factory: creates and configures the QApplication."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.ui import themes
from src.ui.main_window import MainWindow
from src.utils.logging_setup import setup_logging

logger = logging.getLogger(__name__)


class App:
    """Owns the QApplication and the main window lifecycle."""

    def __init__(self, argv: list[str]) -> None:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        self.qt_app = QApplication(argv)
        self.qt_app.setApplicationName("Aegis Keymaster")
        self.qt_app.setOrganizationName("Aegis")
        self.qt_app.setApplicationVersion("0.1.0")

        setup_logging(log_dir=self._log_dir())

        self.theme_mode = themes.ThemeMode.NEON
        self.qt_app.setStyleSheet(
            themes.build_stylesheet(themes.get_theme(self.theme_mode), self.theme_mode)
        )

        self.window = MainWindow(theme_mode=self.theme_mode)
        self.window.theme_changed.connect(self._apply_theme)

    @staticmethod
    def _log_dir() -> Path:
        data_home = Path.home() / ".local" / "share"
        return data_home / "aegis-keymaster" / "logs"

    def _apply_theme(self, mode_name: str) -> None:
        try:
            self.theme_mode = themes.ThemeMode(mode_name.lower())
        except ValueError:
            logger.error("Unknown theme requested: %s", mode_name)
            return
        self.qt_app.setStyleSheet(
            themes.build_stylesheet(themes.get_theme(self.theme_mode), self.theme_mode)
        )
        logger.info("Theme applied: %s", self.theme_mode.value)

    def run(self) -> int:
        self.window.show()
        logger.info("Main window shown")
        return self.qt_app.exec()


def main() -> int:
    app = App(sys.argv)
    return app.run()
