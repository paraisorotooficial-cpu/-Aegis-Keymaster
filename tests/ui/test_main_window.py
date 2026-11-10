"""UI smoke tests: the app must boot and switch themes offscreen."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication
from src.ui import themes
from src.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance() or QApplication([])
    yield app


def test_main_window_boots(qapp: QApplication) -> None:
    window = MainWindow()
    window.show()
    assert window.stack.count() == 4
    pixmap = window.grab()
    assert not pixmap.isNull()


@pytest.mark.parametrize("mode", list(themes.ThemeMode))
def test_stylesheets_build_for_all_themes(mode: themes.ThemeMode) -> None:
    qss = themes.build_stylesheet(themes.get_theme(mode), mode)
    assert qss.strip()


def test_theme_signal_emits(qapp: QApplication) -> None:
    window = MainWindow()
    received: list[str] = []
    window.theme_changed.connect(received.append)
    window.theme_selector.setCurrentIndex(0)
    assert received and received[0] in {"light", "dark", "neon"}
