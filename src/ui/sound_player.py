"""QSoundEffect-based playback for the synthesized sound set."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QObject, QUrl

from src.core.sound import SoundId, ensure_sound_files

logger = logging.getLogger(__name__)

try:
    from PySide6.QtMultimedia import QSoundEffect
except ImportError:  # no PulseAudio/PipeWire on this system
    QSoundEffect = None  # type: ignore[assignment,misc]


class SoundPlayer(QObject):
    """Plays pre-rendered WAVs; degrades to a no-op when audio is unavailable."""

    def __init__(self, cache_dir: Path, volume: float = 0.6, muted: bool = False) -> None:
        super().__init__()
        self._effects: dict[SoundId, QSoundEffect | None] = {}
        self._volume = volume
        self._muted = muted
        self._build(cache_dir)

    def _build(self, cache_dir: Path) -> None:
        if QSoundEffect is None:
            logger.info("No audio backend available; sounds are disabled")
            return
        try:
            paths = ensure_sound_files(cache_dir, self._volume)
        except OSError as exc:
            logger.error("Could not write sound cache: %s", exc)
            return
        for sound, path in paths.items():
            try:
                effect = QSoundEffect(self)
                effect.setSource(QUrl.fromLocalFile(str(path)))
                effect.setVolume(1.0)
                self._effects[sound] = effect
            except RuntimeError as exc:
                logger.error("QSoundEffect unavailable for %s: %s", sound.value, exc)
                self._effects[sound] = None

    def configure(self, volume: float, muted: bool, enabled: bool) -> None:
        self._volume = volume
        self._muted = muted or not enabled

    def play(self, sound: SoundId) -> None:
        if self._muted:
            return
        effect = self._effects.get(sound)
        if effect is None:
            return
        try:
            effect.play()
        except RuntimeError as exc:
            logger.error("Sound playback failed for %s: %s", sound.value, exc)
