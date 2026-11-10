"""Application factory: profiles, settings, main window lifecycle."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.core.persistence import CorruptDataError, ProfileStore
from src.core.user_data import UserData
from src.ui import themes
from src.ui.main_window import MainWindow
from src.utils.logging_setup import setup_logging

logger = logging.getLogger(__name__)

DEFAULT_PROFILE = "default"


class App:
    """Owns the profile store, settings and the main window lifecycle."""

    def __init__(self, argv: list[str]) -> None:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        self.qt_app = QApplication(argv)
        self.qt_app.setApplicationName("Aegis Keymaster")
        self.qt_app.setOrganizationName("Aegis")
        self.qt_app.setApplicationVersion("0.2.0")

        setup_logging(log_dir=self._log_dir())

        self.store = ProfileStore()
        self.user_data = self._load_profile(DEFAULT_PROFILE)

        self.theme_mode = themes.ThemeMode(str(self.user_data.settings["theme"]))
        self.qt_app.setStyleSheet(
            themes.build_stylesheet(themes.get_theme(self.theme_mode), self.theme_mode)
        )

        self.window = MainWindow(theme_mode=self.theme_mode, user_data=self.user_data)
        self.window.theme_changed.connect(self._on_theme_changed)
        self.window.settings_screen.settings_changed.connect(self._on_setting_changed)
        self.window.settings_screen.profile_switched.connect(self._on_profile_switched)
        self.window.test_page.test_completed.connect(self._on_test_completed)

    # -- profile handling ------------------------------------------

    def _load_profile(self, name: str) -> UserData:
        try:
            raw = self.store.load(name)
        except FileNotFoundError:
            self.store.create_profile(name)
            raw = self.store.load(name)
        except CorruptDataError:
            logger.error("Profile %s unreadable; starting with empty data", name)
            raw = {"name": name}
        return UserData.from_dict(raw)

    def save_current_profile(self) -> None:
        try:
            self.store.save(self.user_data.name, self.user_data.to_dict())
        except OSError as exc:
            logger.error("Could not save profile %s: %s", self.user_data.name, exc)

    # -- slots -----------------------------------------------------

    def _on_theme_changed(self, mode_name: str) -> None:
        try:
            self.theme_mode = themes.ThemeMode(mode_name.lower())
        except ValueError:
            logger.error("Unknown theme requested: %s", mode_name)
            return
        self.qt_app.setStyleSheet(
            themes.build_stylesheet(themes.get_theme(self.theme_mode), self.theme_mode)
        )
        self.user_data.settings["theme"] = self.theme_mode.value
        self.save_current_profile()
        logger.info("Theme applied: %s", self.theme_mode.value)

    def _on_setting_changed(self, key: str, value: object) -> None:
        if key == "theme":
            self._on_theme_changed(str(value))
            return
        self.save_current_profile()

    def _on_profile_switched(self, name: str) -> None:
        self.save_current_profile()
        self.user_data = self._load_profile(name)
        self.window.settings_screen.reload_from(self.user_data)
        self.window.progress_screen.attach(self.user_data)
        self._on_theme_changed(str(self.user_data.settings["theme"]))
        logger.info("Switched to profile %s", name)

    def _on_test_completed(self, result: object, key_stats: dict) -> None:
        recorded = self.user_data.record_test(result)  # type: ignore[attr-defined]
        self._update_weak_keys(key_stats)
        if recorded:
            self.save_current_profile()
            self.window.progress_screen.refresh()
            logger.info("Test result saved (%.1f net WPM)", getattr(result, "net_wpm", 0.0))

    def _update_weak_keys(self, key_stats: dict) -> None:
        from src.core.weak_keys import KeyStats

        stored = self.user_data.weak_key_stats
        for key, stats in key_stats.items():
            if not isinstance(stats, KeyStats):
                continue
            entry = stored.setdefault(
                key, {"attempts": 0, "errors": 0, "latency_total": 0.0, "latency_samples": 0}
            )
            entry["attempts"] = int(entry["attempts"]) + stats.attempts
            entry["errors"] = int(entry["errors"]) + stats.errors
            entry["latency_total"] = float(entry["latency_total"]) + stats.latency_total
            entry["latency_samples"] = int(entry["latency_samples"]) + stats.latency_samples

    # -- lifecycle -------------------------------------------------

    @staticmethod
    def _log_dir() -> Path:
        data_home = Path.home() / ".local" / "share"
        return data_home / "aegis-keymaster" / "logs"

    def run(self) -> int:
        self.window.show()
        logger.info("Main window shown")
        exit_code = self.qt_app.exec()
        self.save_current_profile()
        return exit_code


def main() -> int:
    app = App(sys.argv)
    return app.run()
