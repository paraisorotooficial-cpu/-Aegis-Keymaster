"""UI smoke tests for the progress panel."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication
from src.core.stats import Stats
from src.core.typing_test import IntervalStat
from src.core.typing_test import TestResult as ResultModel
from src.core.user_data import UserData
from src.ui.progress_screen import ProgressScreen


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def make_result(net_wpm: float, duration: int = 60) -> ResultModel:
    return ResultModel(
        text="t", typed_text="t", duration_seconds=duration,
        elapsed_seconds=float(duration), total_keystrokes=50, correct_keystrokes=48,
        uncorrected_errors=1, gross_wpm=net_wpm + 2, net_wpm=net_wpm, accuracy=95.0,
        consistency=88.0, valid=True, aborted=False,
        intervals=[IntervalStat(0, 5, 10, 9, 24.0)],
    )


@pytest.fixture
def data() -> UserData:
    user = UserData(name="default")
    for i, wpm in enumerate((20, 25, 30, 35, 40)):
        user.record_test(make_result(wpm))
        user.history[-1]["timestamp"] = (datetime.now() - timedelta(days=i)).isoformat()
    user.weak_key_stats = {
        "e": {"attempts": 10, "errors": 4, "latency_total": 2.0, "latency_samples": 5},
        "r": {"attempts": 8, "errors": 1, "latency_total": 1.0, "latency_samples": 4},
    }
    return user


def test_panel_renders_with_data(qapp: QApplication, data: UserData) -> None:
    panel = ProgressScreen(data)
    panel.resize(900, 700)
    panel.refresh()
    assert panel._summary_labels["tests"].text() == "5"
    assert panel._summary_labels["streak"].text() == "5 d"
    assert panel._table.rowCount() == 5
    assert not panel.grab().isNull()


def test_empty_panel_is_safe(qapp: QApplication) -> None:
    panel = ProgressScreen(UserData())
    panel.resize(900, 700)
    panel.refresh()
    assert panel._table.rowCount() == 0
    assert not panel.grab().isNull()


def test_filters(qapp: QApplication, data: UserData) -> None:
    data.record_test(make_result(70.0, duration=180))
    panel = ProgressScreen(data)
    panel.refresh()
    index = panel._duration_filter.findData(180)
    panel._duration_filter.setCurrentIndex(index)
    assert panel._table.rowCount() == 1
    panel._duration_filter.setCurrentIndex(0)
    assert panel._table.rowCount() == 6


def test_heatmap_toggle(qapp: QApplication, data: UserData) -> None:
    panel = ProgressScreen(data)
    assert panel._heatmap.toggle_metric() is True
    assert panel._heatmap.toggle_metric() is False
    assert not panel._heatmap.grab().isNull()


def test_numbers_match_data(qapp: QApplication, data: UserData) -> None:
    panel = ProgressScreen(data)
    panel.refresh()
    stats = Stats(data)
    expected_minutes = stats.total_practice_seconds() / 60.0
    assert panel._summary_labels["time"].text() == f"{expected_minutes:.0f} min"
    trend = stats.wpm_trend()
    assert len(trend) == 5
    assert trend[-1] == (20 + 25 + 30 + 35 + 40) / 5
