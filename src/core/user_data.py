"""User data model: settings, test history and (later) lesson progress."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.core.persistence import SCHEMA_VERSION
from src.core.typing_test import TestResult

DEFAULT_SETTINGS: dict[str, Any] = {
    "theme": "neon",
    "effects_level": "high",
    "reduce_motion": False,
    "volume": 0.6,
    "muted": False,
    "sound_enabled": True,
    "layout": "auto",
    "ui_language": "es",
    "font_size": 16,
    "cursor_style": "bar",
    "error_mode": "advance",
    "show_keyboard": True,
    "show_hand_diagram": False,
}

KNOWN_DURATIONS = (60, 180, 300)


@dataclass
class UserData:
    """Everything persisted per profile."""

    name: str = "default"
    settings: dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_SETTINGS))
    history: list[dict[str, Any]] = field(default_factory=list)
    lesson_progress: dict[str, Any] = field(default_factory=dict)
    weak_key_stats: dict[str, dict[str, Any]] = field(default_factory=dict)

    # -- serialization ---------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "name": self.name,
            "settings": {**DEFAULT_SETTINGS, **self.settings},
            "history": self.history,
            "lesson_progress": self.lesson_progress,
            "weak_key_stats": self.weak_key_stats,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UserData:
        merged = dict(DEFAULT_SETTINGS)
        merged.update(data.get("settings") or {})
        return cls(
            name=str(data.get("name", "default")),
            settings=merged,
            history=list(data.get("history") or []),
            lesson_progress=dict(data.get("lesson_progress") or {}),
            weak_key_stats=dict(data.get("weak_key_stats") or {}),
        )

    # -- test history ----------------------------------------------

    def record_test(self, result: TestResult) -> bool:
        """Append a valid test result. Returns False for invalid tests."""
        if not result.valid:
            return False
        self.history.append(result.to_dict())
        return True

    def best_for(self, duration: int) -> dict[str, Any] | None:
        """Best (highest net WPM) valid result for a duration."""
        best: dict[str, Any] | None = None
        for entry in self.history:
            if entry.get("duration_seconds") != duration or not entry.get("valid", True):
                continue
            if best is None or entry["net_wpm"] > best["net_wpm"]:
                best = entry
        return best

    def total_practice_seconds(self) -> float:
        return sum(float(entry.get("elapsed_seconds", 0.0)) for entry in self.history)
