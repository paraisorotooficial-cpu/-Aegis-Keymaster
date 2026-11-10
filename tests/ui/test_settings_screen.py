"""UI smoke tests for the settings screen and profile flow."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication
from src.core.persistence import ProfileStore
from src.core.user_data import UserData
from src.ui.settings_screen import SettingsScreen


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.fixture
def store(tmp_path) -> ProfileStore:
    return ProfileStore(base_dir=tmp_path)


def test_renders_current_settings(qapp: QApplication, store: ProfileStore) -> None:
    store.create_profile("default")
    data = UserData.from_dict(store.load("default"))
    screen = SettingsScreen(data)
    screen.resize(800, 700)
    assert not screen.grab().isNull()
    assert screen._theme.currentData() == "neon"


def test_change_emits_signal_and_updates_model(qapp: QApplication, store: ProfileStore) -> None:
    store.create_profile("default")
    data = UserData.from_dict(store.load("default"))
    screen = SettingsScreen(data)
    received: list[tuple[str, object]] = []
    screen.settings_changed.connect(lambda k, v: received.append((k, v)))
    screen._reduce_motion.setChecked(True)
    assert received and received[-1][0] == "reduce_motion"
    assert data.settings["reduce_motion"] is True


def test_theme_change_updates_model(qapp: QApplication, store: ProfileStore) -> None:
    store.create_profile("default")
    data = UserData.from_dict(store.load("default"))
    screen = SettingsScreen(data)
    index = screen._theme.findData("light")
    screen._theme.setCurrentIndex(index)
    assert data.settings["theme"] == "light"


def test_reload_from_refreshes_controls(qapp: QApplication, store: ProfileStore) -> None:
    store.create_profile("default")
    screen = SettingsScreen(UserData(name="default"))
    other = UserData(name="other")
    other.settings["theme"] = "dark"
    other.settings["font_size"] = 20
    screen.reload_from(other)
    assert screen._theme.currentData() == "dark"
    assert screen._font_size.value() == 20


def test_export_json_writes_history(qapp: QApplication, store: ProfileStore, tmp_path) -> None:
    from src.core.typing_test import IntervalStat
    from src.core.typing_test import TestResult as ResultModel
    from src.core.user_data import UserData as Model

    data = Model(name="default")
    data.record_test(
        ResultModel(
            text="t", typed_text="t", duration_seconds=60, elapsed_seconds=60.0,
            total_keystrokes=50, correct_keystrokes=48, uncorrected_errors=1,
            gross_wpm=50.0, net_wpm=48.0, accuracy=96.0, consistency=90.0,
            valid=True, aborted=False,
            intervals=[IntervalStat(0, 5, 10, 9, 24.0)],
        )
    )
    screen = SettingsScreen(data)
    target = tmp_path / "out.json"
    from unittest.mock import patch

    with patch(
        "src.ui.settings_screen.QFileDialog.getSaveFileName", return_value=(str(target), "")
    ):
        screen._export_json()
    assert target.exists()
    assert "net_wpm" in target.read_text(encoding="utf-8")
