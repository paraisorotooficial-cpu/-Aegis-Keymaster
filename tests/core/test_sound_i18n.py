"""Tests for synthesized sounds, i18n and the contrast audit."""

from __future__ import annotations

import io
import struct
import wave

from src.core.i18n import current_language, set_language, tr
from src.core.sound import SoundId, ensure_sound_files, render_wav


def test_render_wav_produces_valid_mono_16bit() -> None:
    data = render_wav(SoundId.KEY, volume=0.5)
    with wave.open(io.BytesIO(data), "rb") as reader:
        assert reader.getnchannels() == 1
        assert reader.getsampwidth() == 2
        assert reader.getframerate() == 44100
        assert reader.getnframes() > 0


def test_all_sounds_render() -> None:
    for sound in SoundId:
        data = render_wav(sound)
        with wave.open(io.BytesIO(data), "rb") as reader:
            assert reader.getnframes() > 100


def test_volume_zero_silences_output() -> None:
    data = render_wav(SoundId.ERROR, volume=0.0)
    with wave.open(io.BytesIO(data), "rb") as reader:
        frames = reader.readframes(reader.getnframes())
        n = reader.getnframes()
    samples = struct.unpack(f"<{n}h", frames)
    assert max(abs(s) for s in samples) == 0


def test_ensure_sound_files_caches(tmp_path) -> None:
    paths = ensure_sound_files(tmp_path, volume=0.5)
    assert set(paths) == set(SoundId)
    for path in paths.values():
        assert path.exists() and path.stat().st_size > 0
    first = paths[SoundId.KEY].read_bytes()
    ensure_sound_files(tmp_path, volume=0.5)
    assert paths[SoundId.KEY].read_bytes() == first
    ensure_sound_files(tmp_path, volume=0.9)
    assert paths[SoundId.KEY].read_bytes() != first


def test_i18n_defaults_to_spanish() -> None:
    set_language("es")
    assert tr("nav.course") == "Curso"
    set_language("en")
    assert tr("nav.course") == "Course"
    set_language("fr")
    assert current_language() == "en"  # unknown codes are ignored
    set_language("es")
    assert tr("nonexistent.key") == "nonexistent.key"
