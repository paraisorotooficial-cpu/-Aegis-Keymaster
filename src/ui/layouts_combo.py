"""Shared helpers for keyboard-layout selection widgets."""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox

from src.core.layouts import available_layouts, detect_layout

LAYOUT_LABELS = {"us": "US", "es": "España (es)", "latam": "Latinoamericano (latam)"}


def fill_layout_combo(
    combo: QComboBox, detected: str | None = None, include_auto: bool = False
) -> None:
    """Fill a combo with available layouts; optionally an 'auto' entry."""
    combo.clear()
    if include_auto:
        combo.addItem("Autodetectar", "auto")
    for name in available_layouts():
        combo.addItem(LAYOUT_LABELS.get(name, name), name)
    if detected is None:
        detected = detect_layout()
    if include_auto:
        combo.setCurrentIndex(0)
    else:
        index = combo.findData(detected)
        combo.setCurrentIndex(max(0, index))


def resolve_layout_name(setting: str) -> str:
    """Map the 'auto' setting to a concrete layout name."""
    return detect_layout() if setting == "auto" else setting
