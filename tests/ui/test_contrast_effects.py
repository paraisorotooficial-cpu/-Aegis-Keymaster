"""Tests for the WCAG contrast audit and the effects controller."""

from __future__ import annotations

import pytest
from src.ui.contrast import audit_all_themes, contrast_ratio, failing_pairs
from src.ui.themes import ThemeMode


def test_known_contrast_value() -> None:
    ratio = contrast_ratio("#000000", "#FFFFFF")
    assert 20.0 < ratio < 21.1
    assert contrast_ratio("#000000", "#000000") == 1.0


def test_all_themes_meet_aa_for_text() -> None:
    for mode in ThemeMode:
        assert failing_pairs(mode) == [], f"{mode.value} fails AA"


def test_audit_all_themes_covers_roles() -> None:
    audit = audit_all_themes()
    assert set(audit) == {"light", "dark", "neon"}
    assert len(audit["neon"]) == 9  # 3 text roles x 3 backgrounds


@pytest.mark.parametrize("level,index", [("high", 0), ("medium", 1), ("low", 2), ("off", 3)])
def test_levels_ordered(level: str, index: int) -> None:
    from src.ui.effects import LEVELS

    assert LEVELS[index] == level


def test_controller_downgrades_on_slow_frames(qapp) -> None:
    from src.ui.effects import EffectsController

    controller = EffectsController("high")
    changes: list[str] = []
    controller.level_changed.connect(changes.append)
    for _ in range(60):
        controller.register_frame(0.030)  # ~33 fps
    assert controller.level == "medium"
    assert changes == ["medium"]


def test_controller_keeps_level_on_fast_frames(qapp) -> None:
    from src.ui.effects import EffectsController

    controller = EffectsController("high")
    for _ in range(200):
        controller.register_frame(0.005)  # 200 fps
    assert controller.level == "high"


def test_controller_downgrades_only_once(qapp) -> None:
    from src.ui.effects import EffectsController

    controller = EffectsController("high")
    for _ in range(60):
        controller.register_frame(0.030)
    for _ in range(60):
        controller.register_frame(0.030)
    assert controller.level == "medium"


def test_controller_off_never_downgrades(qapp) -> None:
    from src.ui.effects import EffectsController

    controller = EffectsController("off")
    for _ in range(60):
        controller.register_frame(0.030)
    assert controller.level == "off"


def test_cursor_and_glow_per_level() -> None:
    from src.ui.effects import cursor_ms, glow_factor

    assert cursor_ms("high") == 90
    assert cursor_ms("low") == 0
    assert glow_factor("high") == 1.0
    assert glow_factor("off") == 0.0
