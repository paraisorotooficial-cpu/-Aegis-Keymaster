"""Tests for statistics derived from history."""

from __future__ import annotations

from datetime import date, timedelta

from src.core.stats import Stats, moving_average
from src.core.typing_test import IntervalStat
from src.core.typing_test import TestResult as ResultModel
from src.core.user_data import UserData


def make_result(net_wpm: float, duration: int = 60, valid: bool = True) -> ResultModel:
    return ResultModel(
        text="t", typed_text="t", duration_seconds=duration,
        elapsed_seconds=float(duration), total_keystrokes=50, correct_keystrokes=48,
        uncorrected_errors=1, gross_wpm=net_wpm + 2, net_wpm=net_wpm, accuracy=95.0,
        consistency=88.0, valid=valid, aborted=False,
        intervals=[IntervalStat(0, 5, 10, 9, 24.0)],
    )


def build_history() -> UserData:
    data = UserData()
    for wpm in (20, 25, 30, 35, 40, 50):
        data.record_test(make_result(wpm))
    return data


class TestMovingAverage:
    def test_basic_window(self) -> None:
        assert moving_average([1, 2, 3, 4], 2) == [1.0, 1.5, 2.5, 3.5]

    def test_window_larger_than_data(self) -> None:
        assert moving_average([2, 4], 10) == [2.0, 3.0]

    def test_empty(self) -> None:
        assert moving_average([], 3) == []

    def test_invalid_window(self) -> None:
        try:
            moving_average([1], 0)
        except ValueError:
            return
        raise AssertionError("expected ValueError")


class TestTrendsAndRecords:
    def test_wpm_trend_smooths(self) -> None:
        stats = Stats(build_history())
        trend = stats.wpm_trend(window=3)
        assert trend[0] == 20.0
        assert trend[-1] == (35 + 40 + 50) / 3

    def test_accuracy_trend(self) -> None:
        stats = Stats(build_history())
        assert stats.accuracy_trend() == [95.0] * 6

    def test_records_by_duration(self) -> None:
        data = build_history()
        data.record_test(make_result(70.0, duration=180))
        stats = Stats(data)
        records = stats.records_by_duration()
        assert records[60]["net_wpm"] == 50.0
        assert records[180]["net_wpm"] == 70.0
        assert 300 not in records

    def test_totals(self) -> None:
        stats = Stats(build_history())
        assert stats.total_tests() == 6
        assert stats.total_practice_seconds() == 360.0


class TestStreak:
    def test_no_history(self) -> None:
        assert Stats(UserData()).day_streak() == 0

    def test_today_counts(self) -> None:
        data = UserData()
        data.record_test(make_result(30.0))
        entry = data.history[-1]
        from datetime import datetime

        entry["timestamp"] = datetime.now().isoformat()
        assert Stats(data).day_streak() == 1

    def test_consecutive_days(self) -> None:
        from datetime import datetime

        data = UserData()
        today = date.today()
        for offset in (0, 1, 2):
            data.record_test(make_result(30.0))
            data.history[-1]["timestamp"] = datetime.combine(
                today - timedelta(days=offset), datetime.min.time()
            ).isoformat()
        assert Stats(data).day_streak() == 3

    def test_gap_breaks_streak(self) -> None:
        from datetime import datetime

        data = UserData()
        today = date.today()
        for offset in (0, 2):
            data.record_test(make_result(30.0))
            data.history[-1]["timestamp"] = datetime.combine(
                today - timedelta(days=offset), datetime.min.time()
            ).isoformat()
        assert Stats(data).day_streak() == 1

    def test_stale_history_is_zero(self) -> None:
        from datetime import datetime

        data = UserData()
        data.record_test(make_result(30.0))
        data.history[-1]["timestamp"] = datetime(2020, 1, 1).isoformat()
        assert Stats(data).day_streak() == 0


class TestFiltering:
    def test_filter_by_duration(self) -> None:
        data = build_history()
        data.record_test(make_result(70.0, duration=180))
        stats = Stats(data)
        assert len(stats.filter_history(duration=180)) == 1
        assert len(stats.filter_history(duration=60)) == 6

    def test_filter_by_mode(self) -> None:
        data = build_history()
        data.history[0]["mode"] = "lesson"
        stats = Stats(data)
        assert len(stats.filter_history(mode="lesson")) == 1
        assert len(stats.filter_history(mode="test")) == 5

    def test_filter_by_day(self) -> None:
        from datetime import datetime

        data = build_history()
        data.history[0]["timestamp"] = datetime(2020, 1, 1, 10).isoformat()
        stats = Stats(data)
        assert len(stats.filter_history(day=date(2020, 1, 1))) == 1


class TestHeatmap:
    def test_empty(self) -> None:
        assert Stats(UserData()).heatmap() == {}

    def test_rates_and_latency(self) -> None:
        data = UserData()
        data.weak_key_stats = {
            "e": {"attempts": 10, "errors": 3, "latency_total": 2.0, "latency_samples": 4},
        }
        heatmap = Stats(data).heatmap()
        assert heatmap["e"]["error_rate"] == 0.3
        assert heatmap["e"]["avg_latency"] == 0.5

    def test_zero_attempts_safe(self) -> None:
        data = UserData()
        data.weak_key_stats = {"q": {"attempts": 0, "errors": 0}}
        assert Stats(data).heatmap()["q"]["error_rate"] == 0.0
