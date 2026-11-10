"""Statistics derived from a profile's test history (pure logic, no Qt)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from src.core.user_data import KNOWN_DURATIONS, UserData


def moving_average(values: list[float], window: int = 5) -> list[float]:
    """Trailing moving average; early points average what exists."""
    if window <= 0:
        raise ValueError("window must be positive")
    result: list[float] = []
    for i in range(len(values)):
        chunk = values[max(0, i - window + 1) : i + 1]
        result.append(sum(chunk) / len(chunk))
    return result


def parse_date(value: str) -> date | None:
    try:
        return datetime.fromisoformat(value).date()
    except (TypeError, ValueError):
        return None


class Stats:
    """Read-only views over UserData history."""

    def __init__(self, user_data: UserData) -> None:
        self.user_data = user_data

    # -- trends ----------------------------------------------------

    def wpm_trend(self, window: int = 5) -> list[float]:
        return moving_average([float(e["net_wpm"]) for e in self.user_data.history], window)

    def accuracy_trend(self, window: int = 5) -> list[float]:
        return moving_average([float(e["accuracy"]) for e in self.user_data.history], window)

    # -- records ---------------------------------------------------

    def records_by_duration(self) -> dict[int, dict[str, Any]]:
        return {
            duration: best
            for duration in KNOWN_DURATIONS
            if (best := self.user_data.best_for(duration)) is not None
        }

    def total_practice_seconds(self) -> float:
        return self.user_data.total_practice_seconds()

    def total_tests(self) -> int:
        return len(self.user_data.history)

    # -- streak ----------------------------------------------------

    def day_streak(self, today: date | None = None) -> int:
        """Consecutive days (ending today or yesterday) with at least one test."""
        days = {
            d
            for entry in self.user_data.history
            if (d := parse_date(str(entry.get("timestamp", "")))) is not None
        }
        if not days:
            return 0
        today = today or date.today()
        if today not in days and (today - timedelta(days=1)) not in days:
            return 0
        streak = 0
        cursor = today if today in days else today - timedelta(days=1)
        while cursor in days:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    # -- filtering -------------------------------------------------

    def filter_history(
        self,
        mode: str | None = None,
        duration: int | None = None,
        day: date | None = None,
    ) -> list[dict[str, Any]]:
        result = []
        for entry in self.user_data.history:
            if mode is not None and entry.get("mode", "test") != mode:
                continue
            if duration is not None and entry.get("duration_seconds") != duration:
                continue
            if day is not None:
                entry_day = parse_date(str(entry.get("timestamp", "")))
                if entry_day != day:
                    continue
            result.append(entry)
        return result

    # -- heatmap ---------------------------------------------------

    def heatmap(self) -> dict[str, dict[str, float]]:
        """Per-key error rate and average latency from persisted weak-key stats."""
        output: dict[str, dict[str, float]] = {}
        for key, raw in self.user_data.weak_key_stats.items():
            attempts = int(raw.get("attempts", 0))
            errors = int(raw.get("errors", 0))
            samples = int(raw.get("latency_samples", 0))
            output[key] = {
                "error_rate": errors / attempts if attempts else 0.0,
                "avg_latency": raw.get("latency_total", 0.0) / samples if samples else 0.0,
                "attempts": attempts,
            }
        return output
