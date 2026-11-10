"""Sound synthesis: small WAV effects generated in code (no network, no assets).

Sounds are rendered as in-memory WAV bytes with the standard library and
cached as files so QSoundEffect can play them.
"""

from __future__ import annotations

import io
import math
import random
import struct
import wave
from enum import Enum
from pathlib import Path

SAMPLE_RATE = 44100


class SoundId(Enum):
    KEY = "key"
    ERROR = "error"
    PASS = "pass"
    TEST_END = "test_end"


def _sine(freq: float, seconds: float, amplitude: float) -> list[float]:
    total = int(SAMPLE_RATE * seconds)
    frames = []
    for i in range(total):
        fade_in = min(1.0, i / (0.01 * SAMPLE_RATE)) if seconds > 0.05 else 1.0
        fade_out = min(1.0, (total - i) / (0.02 * SAMPLE_RATE))
        frames.append(
            amplitude * fade_in * fade_out * math.sin(2 * math.pi * freq * i / SAMPLE_RATE)
        )
    return frames


def _noise_click(seconds: float, amplitude: float) -> list[float]:
    rng = random.Random(7)
    n = int(SAMPLE_RATE * seconds)
    out = [0.0] * n
    previous = 0.0
    for i in range(n):
        previous = 0.7 * previous + 0.3 * rng.uniform(-1.0, 1.0)
        decay = math.exp(-i / (0.002 * SAMPLE_RATE))
        out[i] = amplitude * decay * previous
    return out


def _render_key() -> list[float]:
    click = _noise_click(0.012, 0.5)
    body = _sine(1900.0, 0.012, 0.25)
    return [c + b for c, b in zip(click, body, strict=False)]


def _render_error() -> list[float]:
    low = _sine(140.0, 0.12, 0.6)
    buzz = _sine(280.0, 0.12, 0.2)
    return [0.6 * a + b for a, b in zip(low, buzz, strict=False)]


def _render_pass() -> list[float]:
    frames: list[float] = []
    for freq in (523.25, 659.25, 783.99):
        frames.extend(_sine(freq, 0.11, 0.5))
    return frames


def _render_test_end() -> list[float]:
    frames = _sine(660.0, 0.15, 0.5)
    frames.extend(_sine(440.0, 0.22, 0.5))
    return frames


_RENDERERS = {
    SoundId.KEY: _render_key,
    SoundId.ERROR: _render_error,
    SoundId.PASS: _render_pass,
    SoundId.TEST_END: _render_test_end,
}


def render_wav(sound: SoundId, volume: float = 0.6) -> bytes:
    """Render a sound as 16-bit mono WAV bytes."""
    amplitude = max(0.0, min(1.0, volume))
    frames = [max(-1.0, min(1.0, sample * amplitude)) for sample in _RENDERERS[sound]()]
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(SAMPLE_RATE)
        writer.writeframes(b"".join(struct.pack("<h", int(s * 32767)) for s in frames))
    return buffer.getvalue()


def ensure_sound_files(directory: Path, volume: float = 0.6) -> dict[SoundId, Path]:
    """Write the WAV cache (only when missing or volume changed) and return paths."""
    directory.mkdir(parents=True, exist_ok=True)
    stamp = directory / ".volume"
    regenerate = not stamp.exists() or stamp.read_text().strip() != f"{volume:.3f}"
    paths: dict[SoundId, Path] = {}
    for sound in SoundId:
        path = directory / f"{sound.value}.wav"
        if regenerate or not path.exists():
            path.write_bytes(render_wav(sound, volume))
        paths[sound] = path
    stamp.write_text(f"{volume:.3f}\n")
    return paths
