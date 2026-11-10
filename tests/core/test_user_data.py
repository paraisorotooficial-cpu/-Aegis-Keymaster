"""Tests for the user data model."""

from __future__ import annotations

from src.core.typing_test import IntervalStat
from src.core.typing_test import TestResult as ResultModel
from src.core.user_data import DEFAULT_SETTINGS, UserData


def make_result(net_wpm: float, duration: int = 60, valid: bool = True) -> ResultModel:
    return ResultModel(
        text="texto",
        typed_text="texto",
        duration_seconds=duration,
        elapsed_seconds=float(duration),
        total_keystrokes=50,
        correct_keystrokes=48,
        uncorrected_errors=1,
        gross_wpm=net_wpm + 2,
        net_wpm=net_wpm,
        accuracy=96.0,
        consistency=90.0,
        valid=valid,
        aborted=False,
        intervals=[IntervalStat(0, 5, 10, 9, 24.0)],
    )


class TestUserData:
    def test_defaults_are_complete(self) -> None:
        data = UserData()
        assert data.settings["theme"] == "neon"
        assert data.settings["error_mode"] == "advance"
        assert data.settings["ui_language"] == "es"

    def test_roundtrip_preserves_everything(self) -> None:
        data = UserData(name="Ana")
        data.record_test(make_result(42.0))
        data.settings["font_size"] = 18
        restored = UserData.from_dict(data.to_dict())
        assert restored.name == "Ana"
        assert restored.settings["font_size"] == 18
        assert restored.history[0]["net_wpm"] == 42.0

    def test_from_dict_with_missing_fields(self) -> None:
        data = UserData.from_dict({"name": "x"})
        assert data.settings == DEFAULT_SETTINGS
        assert data.history == []

    def test_invalid_tests_are_not_recorded(self) -> None:
        data = UserData()
        assert data.record_test(make_result(10.0, valid=False)) is False
        assert data.history == []

    def test_valid_tests_are_recorded(self) -> None:
        data = UserData()
        assert data.record_test(make_result(40.0)) is True
        assert len(data.history) == 1

    def test_best_for_returns_highest_wpm(self) -> None:
        data = UserData()
        data.record_test(make_result(30.0))
        data.record_test(make_result(55.0))
        data.record_test(make_result(45.0))
        assert data.best_for(60)["net_wpm"] == 55.0

    def test_best_for_isolated_by_duration(self) -> None:
        data = UserData()
        data.record_test(make_result(30.0, duration=60))
        data.record_test(make_result(70.0, duration=300))
        assert data.best_for(60)["net_wpm"] == 30.0
        assert data.best_for(300)["net_wpm"] == 70.0
        assert data.best_for(180) is None

    def test_total_practice_seconds(self) -> None:
        data = UserData()
        data.record_test(make_result(30.0, duration=60))
        data.record_test(make_result(40.0, duration=180))
        assert data.total_practice_seconds() == 240.0
