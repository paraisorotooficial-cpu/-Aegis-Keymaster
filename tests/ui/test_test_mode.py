"""UI smoke tests for the timed test flow (setup → live → report)."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication
from src.core.typing_test import TestResult as ResultData
from src.ui.test_mode import TestPage as PageWidget


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_setup_screen_renders(qapp: QApplication) -> None:
    page = PageWidget()
    page.resize(900, 600)
    assert page._stack.count() == 3
    assert not page.grab().isNull()


def test_full_60s_flow_produces_report(qapp: QApplication) -> None:
    page = PageWidget()
    page.resize(900, 600)
    page._on_start(60, "es")
    session = page._live._session
    assert session is not None
    for char in session.text[:20]:
        session.type_char(char)
    page._live._refresh()
    assert not page._live.grab().isNull()
    session.abort()
    page._live._stop()
    assert page._stack.currentIndex() == 2
    assert not page._report.grab().isNull()


def test_report_shows_invalid_warning(qapp: QApplication) -> None:
    page = PageWidget()
    page._on_start(60, "es")
    session = page._live._session
    assert session is not None
    for char in session.text[:5]:
        session.type_char(char)
    result, key_stats = page._live._session.abort(), page._live._session.key_stats()
    page._report.show_result(result, 60, "es")
    page._report.attach_key_stats(key_stats)
    assert not page._report._warning.isHidden()
    assert isinstance(result, ResultData)
    assert result.valid is False


def test_repeat_button_returns_to_live(qapp: QApplication) -> None:
    page = PageWidget()
    page._on_start(60, "es")
    page._live._session.abort()
    page._live._stop()
    page._report.repeat_requested.emit()
    assert page._stack.currentIndex() == 1
