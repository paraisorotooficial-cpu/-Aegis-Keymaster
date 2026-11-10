"""Application factory: profiles, settings, main window lifecycle."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.core import i18n
from src.core.layouts import load_layout
from src.core.lessons import LessonManager
from src.core.persistence import CorruptDataError, ProfileStore
from src.core.sound import SoundId
from src.core.user_data import UserData
from src.ui import themes
from src.ui.effects import EffectsController
from src.ui.layouts_combo import resolve_layout_name
from src.ui.main_window import MainWindow
from src.ui.onboarding import OnboardingDialog
from src.ui.sound_player import SoundPlayer
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

        self.lesson_manager = LessonManager(layout=load_layout(self._active_layout_name()))
        i18n.set_language(str(self.user_data.settings["ui_language"]))
        self.window = MainWindow(
            theme_mode=self.theme_mode, user_data=self.user_data, lesson_manager=self.lesson_manager
        )
        self.window.theme_changed.connect(self._on_theme_changed)
        self.window.settings_screen.settings_changed.connect(self._on_setting_changed)
        self.window.settings_screen.profile_switched.connect(self._on_profile_switched)
        self.window.test_page.test_completed.connect(self._on_test_completed)
        self.window.course_page.lesson_completed.connect(self._on_lesson_completed)
        self.window.course_page.review_drill_requested.connect(self._open_weak_key_drill)
        self.window.set_layout_name(self._active_layout_name())
        self.window.course_page.refresh(self.user_data.lesson_progress)

        self.sound_player = SoundPlayer(
            self._cache_dir(),
            volume=float(self.user_data.settings["volume"]),
            muted=bool(self.user_data.settings["muted"])
            or not bool(self.user_data.settings["sound_enabled"]),
        )
        self.effects = EffectsController(
            str(self.user_data.settings["effects_level"]),
            bool(self.user_data.settings["reduce_motion"]),
        )
        self.window.set_sound_player(self.sound_player)
        self.window.apply_effects(self.effects)
        self.window.test_page.test_completed.connect(
            lambda _result, _stats: self.sound_player.play(SoundId.TEST_END)
        )
        self.window.course_page.lesson_completed.connect(self._play_lesson_sound)

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
        if key == "ui_language":
            i18n.set_language(str(value))
            self.window.retranslate()
            self.save_current_profile()
            return
        if key in ("volume", "muted", "sound_enabled"):
            self.sound_player.configure(
                volume=float(self.user_data.settings["volume"]),
                muted=bool(self.user_data.settings["muted"]),
                enabled=bool(self.user_data.settings["sound_enabled"]),
            )
            self.save_current_profile()
            return
        if key in ("effects_level", "reduce_motion"):
            self.effects.set_level(str(self.user_data.settings["effects_level"]))
            self.window.apply_effects(self.effects)
            self.save_current_profile()
            return
        if key == "layout":
            name = self._active_layout_name()
            self.lesson_manager.layout = load_layout(name)
            self.window.set_layout_name(name)
            self.save_current_profile()
            return
        if key == "show_keyboard":
            self.window.set_keyboard_visible(bool(value))
            self.save_current_profile()
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

    def _on_lesson_completed(
        self, lesson_id: str, wpm: float, accuracy: float, stars: int, key_stats: dict
    ) -> None:
        lesson = next(
            (item for item in self.lesson_manager.lessons if item.id == lesson_id), None
        )
        if lesson is None:
            logger.error("Unknown lesson id reported: %s", lesson_id)
            return
        progress = self.user_data.lesson_progress
        entry = self.lesson_manager.record_result(lesson, wpm, accuracy, progress)
        self._update_weak_keys(key_stats)
        self.save_current_profile()
        logger.info(
            "Lesson %s finished: %.1f WPM, %.1f%%, %d stars",
            lesson_id, wpm, accuracy, entry["stars"],
        )

    def _play_lesson_sound(
        self, _lesson_id: str, _wpm: float, _accuracy: float, stars: int, _stats: dict
    ) -> None:
        self.sound_player.play(SoundId.PASS if stars >= 1 else SoundId.ERROR)

    def _open_weak_key_drill(self) -> None:
        from src.core.weak_keys import WeakKeyTracker

        tracker = WeakKeyTracker.from_dict(self.user_data.weak_key_stats)
        drill = tracker.generate_drill(length=140)
        self.window.course_page.open_review(drill)

    def _active_layout_name(self) -> str:
        return resolve_layout_name(str(self.user_data.settings["layout"]))

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

    @staticmethod
    def _cache_dir() -> Path:
        data_home = Path.home() / ".local" / "share"
        return data_home / "aegis-keymaster" / "cache" / "sounds"

    def run(self) -> int:
        if not self.user_data.settings.get("onboarded"):
            self._run_onboarding()
        self.window.show()
        logger.info("Main window shown")
        exit_code = self.qt_app.exec()
        self.save_current_profile()
        return exit_code

    def _run_onboarding(self) -> None:
        dialog = OnboardingDialog(
            self._active_layout_name(), str(self.user_data.settings["ui_language"])
        )
        dialog.completed.connect(self._on_onboarding_completed)
        dialog.exec()

    def _on_onboarding_completed(self, result: dict) -> None:
        self.user_data.settings["ui_language"] = result.get("ui_language", "es")
        self.user_data.settings["layout"] = result.get("layout", "auto")
        self.user_data.settings["onboarded"] = True
        self.save_current_profile()
        self.window.set_layout_name(self._active_layout_name())
        self.window.course_page.refresh(self.user_data.lesson_progress)
        logger.info("Onboarding completed: %s", result)


def main() -> int:
    app = App(sys.argv)
    return app.run()
