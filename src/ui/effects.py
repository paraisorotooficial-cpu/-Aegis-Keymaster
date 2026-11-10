"""Effects levels and automatic degradation when the frame budget is missed."""

from __future__ import annotations

import logging
import time
from collections import deque

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)

LEVELS = ("high", "medium", "low", "off")
MIN_FPS = 45.0
WINDOW_SECONDS = 5.0
MIN_SAMPLES = 30

# Cursor glide duration per level (ms); 0 = instant.
CURSOR_MS = {"high": 90, "medium": 60, "low": 0, "off": 0}
# Glow strength multiplier per level.
GLOW = {"high": 1.0, "medium": 0.6, "low": 0.25, "off": 0.0}


def cursor_ms(level: str) -> int:
    return CURSOR_MS.get(level, 90)


def glow_factor(level: str) -> float:
    return GLOW.get(level, 1.0)


class EffectsController(QObject):
    """Tracks frame-time samples and downgrades the level once when fps sag."""

    level_changed = Signal(str)

    def __init__(self, level: str = "high", reduce_motion: bool = False) -> None:
        super().__init__()
        self._level = level if level in LEVELS else "high"
        self._reduce_motion = reduce_motion
        self._samples: deque[tuple[float, float]] = deque()
        self._announced = False

    @property
    def level(self) -> str:
        return self._level

    def set_level(self, level: str) -> None:
        if level in LEVELS and level != self._level:
            self._level = level
            self._samples.clear()
            self.level_changed.emit(level)

    def register_frame(self, seconds: float) -> None:
        """Register one frame time; evaluates degradation over a sliding window."""
        now = time.monotonic()
        self._samples.append((now, seconds))
        while self._samples and now - self._samples[0][0] > WINDOW_SECONDS:
            self._samples.popleft()
        if len(self._samples) < MIN_SAMPLES or self._announced or self._level == "off":
            return
        average = sum(s for _, s in self._samples) / len(self._samples)
        if average > 1.0 / MIN_FPS:
            index = LEVELS.index(self._level)
            if index < len(LEVELS) - 1:
                new_level = LEVELS[index + 1]
                logger.warning(
                    "Average frame time %.1f ms is below 45 fps; lowering effects to %s",
                    average * 1000,
                    new_level,
                )
                self.set_level(new_level)
                self._announced = True
