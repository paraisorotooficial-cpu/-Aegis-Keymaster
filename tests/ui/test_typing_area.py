"""UI smoke tests for the typing area."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication
from src.ui import themes
from src.ui.typing_area import TypingArea


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_load_and_grab(qapp: QApplication) -> None:
    area = TypingArea()
    area.resize(600, 160)
    area.load("hola mundo ñ á ¿")
    pixmap = area.grab()
    assert not pixmap.isNull()


def test_keypress_emits_signal(qapp: QApplication) -> None:
    area = TypingArea()
    area.load("abc")
    received: list[str] = []
    area.keyPressed.connect(received.append)
    area.setFocus()
    from PySide6.QtCore import QEvent, Qt
    from PySide6.QtGui import QKeyEvent

    event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier, "a")
    area.keyPressEvent(event)
    assert received == ["a"]


def test_backspace_emits_signal(qapp: QApplication) -> None:
    area = TypingArea()
    area.load("abc")
    hits: list[bool] = []
    area.backspacePressed.connect(lambda: hits.append(True))
    from PySide6.QtCore import QEvent, Qt
    from PySide6.QtGui import QKeyEvent

    event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Backspace, Qt.KeyboardModifier.NoModifier)
    area.keyPressEvent(event)
    assert hits == [True]


def test_update_state_recolors(qapp: QApplication) -> None:
    area = TypingArea()
    area.load("abc")
    area.update_state(2, ["correct", "incorrect", "pending"])
    assert area._states[0] == "correct"
    assert area.grab() and not area.grab().isNull()


@pytest.mark.parametrize("mode", list(themes.ThemeMode))
def test_theme_switch(qapp: QApplication, mode: themes.ThemeMode) -> None:
    area = TypingArea()
    area.load("texto")
    area.set_theme(mode)
    assert not area.grab().isNull()
