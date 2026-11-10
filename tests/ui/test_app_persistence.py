"""End-to-end persistence tests: settings survive restart, profiles isolate."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication
from src.core.persistence import ProfileStore
from src.core.user_data import UserData


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_settings_survive_restart(tmp_path) -> None:
    store = ProfileStore(base_dir=tmp_path)
    store.create_profile("default")
    data = UserData.from_dict(store.load("default"))
    data.settings["theme"] = "dark"
    data.settings["volume"] = 0.3
    store.save("default", data.to_dict())

    reloaded = UserData.from_dict(store.load("default"))
    assert reloaded.settings["theme"] == "dark"
    assert reloaded.settings["volume"] == 0.3


def test_test_results_survive_restart(tmp_path) -> None:
    from src.core.typing_test import IntervalStat
    from src.core.typing_test import TestResult as ResultModel

    store = ProfileStore(base_dir=tmp_path)
    store.create_profile("default")
    data = UserData.from_dict(store.load("default"))
    result = ResultModel(
        text="t", typed_text="t", duration_seconds=60, elapsed_seconds=60.0,
        total_keystrokes=50, correct_keystrokes=48, uncorrected_errors=1,
        gross_wpm=50.0, net_wpm=48.0, accuracy=96.0, consistency=90.0,
        valid=True, aborted=False, intervals=[IntervalStat(0, 5, 10, 9, 24.0)],
    )
    assert data.record_test(result) is True
    store.save("default", data.to_dict())

    reloaded = UserData.from_dict(store.load("default"))
    assert reloaded.best_for(60)["net_wpm"] == 48.0


def test_corrupt_profile_does_not_crash_app(tmp_path) -> None:
    store = ProfileStore(base_dir=tmp_path)
    store.create_profile("default")
    path = store.profile_path("default")
    path.write_text("garbage{", encoding="utf-8")
    from src.core.persistence import CorruptDataError

    with pytest.raises(CorruptDataError):
        store.load("default")


def test_profile_switch_isolates_data(tmp_path) -> None:
    store = ProfileStore(base_dir=tmp_path)
    store.create_profile("ana")
    store.create_profile("luis")
    ana = UserData.from_dict(store.load("ana"))
    ana.settings["theme"] = "light"
    store.save("ana", ana.to_dict())

    luis = UserData.from_dict(store.load("luis"))
    assert luis.settings["theme"] == "neon"
