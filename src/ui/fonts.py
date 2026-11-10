"""Bundled font loading (DejaVu Sans + DejaVu Sans Mono, free license included)."""

from __future__ import annotations

import logging
from importlib import resources

from PySide6.QtGui import QFont, QFontDatabase

logger = logging.getLogger(__name__)

UI_FAMILY = "DejaVu Sans"
MONO_FAMILY = "DejaVu Sans Mono"
TITLE_SIZE = 22
SUBTITLE_SIZE = 13

_FONT_FILES = (
    "DejaVuSans.ttf",
    "DejaVuSans-Bold.ttf",
    "DejaVuSansMono.ttf",
    "DejaVuSansMono-Bold.ttf",
)


def load_app_fonts() -> tuple[str, str]:
    """Register the bundled fonts with Qt; returns (ui_family, mono_family)."""
    loaded = 0
    for name in _FONT_FILES:
        try:
            path = resources.files("src.assets.fonts") / name
            font_id = QFontDatabase.addApplicationFont(str(path))
            if font_id < 0:
                logger.warning("Font %s could not be registered", name)
            else:
                loaded += 1
        except (FileNotFoundError, OSError) as exc:
            logger.warning("Font %s unavailable: %s", name, exc)
    if loaded == 0:
        logger.warning("No bundled fonts loaded; falling back to system fonts")
    return UI_FAMILY, MONO_FAMILY


def apply_application_font(qt_app, size: int) -> None:
    ui_family, _ = load_app_fonts()
    qt_app.setFont(QFont(ui_family, size))


def title_font() -> QFont:
    font = QFont(UI_FAMILY, TITLE_SIZE)
    font.setWeight(QFont.Weight.Bold)
    return font


def subtitle_font() -> QFont:
    return QFont(UI_FAMILY, SUBTITLE_SIZE)


def mono_font(size: int = 16, bold: bool = False) -> QFont:
    font = QFont(MONO_FAMILY, size, weight=QFont.Weight.Bold if bold else QFont.Weight.Normal)
    font.setStyleHint(QFont.StyleHint.Monospace)
    return font
