"""Tests for the keyboard layout data layer."""

from __future__ import annotations

import pytest
from src.core.layouts import (
    LayoutError,
    _parse,
    available_layouts,
    detect_layout,
    load_layout,
)


def test_load_all_bundled_layouts() -> None:
    assert set(available_layouts()) >= {"us", "es", "latam"}
    for name in available_layouts():
        layout = load_layout(name)
        assert layout.name == name
        assert layout.spec(" ") is not None


def test_us_has_no_enye_but_es_and_latam_do() -> None:
    us = load_layout("us")
    assert us.spec("ñ") is None
    for name in ("es", "latam"):
        spec = load_layout(name).spec("ñ")
        assert spec is not None
        assert spec.row == 2


def test_latam_has_open_question_and_exclamation() -> None:
    latam = load_layout("latam")
    assert latam.spec("¿") is not None
    placement = latam.placement("¡")
    assert placement is not None
    assert placement.base == "¿"
    assert placement.needs_shift


def test_at_is_altgr_q_on_es_and_latam() -> None:
    for name in ("es", "latam"):
        layout = load_layout(name)
        placement = layout.placement("@")
        assert placement is not None
        assert placement.base == "q"
        assert placement.needs_altgr
        assert not placement.needs_shift


def test_dead_acute_composition() -> None:
    for name in ("es", "latam"):
        layout = load_layout(name)
        assert layout.compose("´", "a") == "á"
        assert layout.compose("´", "e") == "é"
        assert layout.compose("´", "u") == "ú"
        assert layout.compose("´", "x") is None


def test_dead_grave_and_diaeresis_on_es() -> None:
    es = load_layout("es")
    assert es.compose("`", "e") == "è"
    assert es.compose("¨", "u") == "ü"


def test_us_has_no_dead_keys() -> None:
    us = load_layout("us")
    assert us.dead_keys == {}
    assert us.compose("´", "a") is None


def test_reverse_lookup_shift() -> None:
    es = load_layout("es")
    placement = es.placement("A")
    assert placement is not None
    assert placement.base == "a"
    assert placement.needs_shift


def test_load_unknown_layout_raises() -> None:
    with pytest.raises(LayoutError):
        load_layout("dvorak")


def test_load_rejects_path_traversal() -> None:
    with pytest.raises(LayoutError):
        load_layout("../secrets")


def test_parse_missing_space_raises() -> None:
    with pytest.raises(LayoutError):
        _parse({"name": "bad", "keys": {"a": {"row": 0, "finger": 0, "shift": "A"}}})


def test_detect_layout_returns_known_layout() -> None:
    assert detect_layout() in available_layouts()
