"""Persistence tests: atomicity, .bak recovery, corruption, migration, failures."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from src.core.persistence import (
    SCHEMA_VERSION,
    CorruptDataError,
    ProfileStore,
    StorageError,
    atomic_write_json,
    migrate,
    read_json_with_recovery,
)


@pytest.fixture
def store(tmp_path: Path) -> ProfileStore:
    return ProfileStore(base_dir=tmp_path)


class TestAtomicWrite:
    def test_writes_exact_content(self, tmp_path: Path) -> None:
        target = tmp_path / "data" / "profile.json"
        atomic_write_json(target, {"schema_version": SCHEMA_VERSION, "name": "x"})
        assert json.loads(target.read_text(encoding="utf-8"))["name"] == "x"

    def test_no_temp_file_left_behind(self, tmp_path: Path) -> None:
        target = tmp_path / "profile.json"
        atomic_write_json(target, {"a": 1})
        assert list(tmp_path.glob("*.tmp")) == []

    def test_keeps_bak_of_previous_content(self, tmp_path: Path) -> None:
        target = tmp_path / "profile.json"
        atomic_write_json(target, {"version": 1})
        atomic_write_json(target, {"version": 2})
        bak = target.with_suffix(".json.bak")
        assert json.loads(bak.read_text(encoding="utf-8"))["version"] == 1

    def test_full_disk_keeps_original(self, tmp_path: Path, monkeypatch) -> None:
        target = tmp_path / "profile.json"
        atomic_write_json(target, {"version": 1})

        def failing_replace(src, dst):
            raise OSError(28, "No space left on device")

        monkeypatch.setattr(os, "replace", failing_replace)
        with pytest.raises(StorageError):
            atomic_write_json(target, {"version": 2})
        assert json.loads(target.read_text(encoding="utf-8"))["version"] == 1
        assert list(tmp_path.glob("*.tmp")) == []

    def test_interrupted_write_keeps_original(self, tmp_path: Path, monkeypatch) -> None:
        target = tmp_path / "profile.json"
        atomic_write_json(target, {"version": 1})

        real_open = open

        def crashing_open(file, mode="r", *args, **kwargs):
            handle = real_open(file, mode, *args, **kwargs)
            if str(file).endswith(".tmp") and "w" in mode:
                original_write = handle.write

                def write(data):
                    original_write(data[: len(data) // 2])
                    raise OSError(5, "Input/output error")

                handle.write = write
            return handle

        monkeypatch.setattr("builtins.open", crashing_open)
        with pytest.raises(StorageError):
            atomic_write_json(target, {"version": 2})
        assert json.loads(target.read_text(encoding="utf-8"))["version"] == 1
        monkeypatch.undo()
        atomic_write_json(target, {"version": 3})
        assert json.loads(target.read_text(encoding="utf-8"))["version"] == 3


class TestRecovery:
    def test_corrupt_main_recovers_from_bak(self, tmp_path: Path) -> None:
        target = tmp_path / "profile.json"
        atomic_write_json(target, {"good": True})
        atomic_write_json(target, {"good": False})
        target.write_text("{corrupt", encoding="utf-8")
        data, recovered = read_json_with_recovery(target)
        assert recovered is True
        assert data == {"good": True}  # .bak holds the previous good copy

    def test_both_corrupt_raises(self, tmp_path: Path) -> None:
        target = tmp_path / "profile.json"
        atomic_write_json(target, {"a": 1})
        atomic_write_json(target, {"a": 2})
        target.write_text("{{{", encoding="utf-8")
        target.with_suffix(".json.bak").write_text("]]]", encoding="utf-8")
        with pytest.raises(CorruptDataError):
            read_json_with_recovery(target)

    def test_missing_file_raises_filenotfound(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            read_json_with_recovery(tmp_path / "nope.json")

    def test_non_dict_content_is_corrupt(self, tmp_path: Path) -> None:
        target = tmp_path / "profile.json"
        target.write_text("[1, 2, 3]", encoding="utf-8")
        with pytest.raises(CorruptDataError):
            read_json_with_recovery(target)


class TestMigration:
    def test_current_version_untouched(self) -> None:
        data = {"schema_version": SCHEMA_VERSION, "name": "x"}
        assert migrate(dict(data)) == data

    def test_old_version_gets_migrated(self) -> None:
        from src.core import persistence

        persistence.MIGRATIONS[0] = lambda d: {**d, "migrated": True, "schema_version": 1}
        try:
            result = migrate({"schema_version": 0})
            assert result["migrated"] is True
            assert result["schema_version"] == SCHEMA_VERSION
        finally:
            del persistence.MIGRATIONS[0]

    def test_missing_version_defaults_to_zero(self) -> None:
        from src.core import persistence

        persistence.MIGRATIONS[0] = lambda d: {**d, "schema_version": 1}
        try:
            result = migrate({})
            assert result["schema_version"] == SCHEMA_VERSION
        finally:
            del persistence.MIGRATIONS[0]

    def test_future_version_raises(self) -> None:
        with pytest.raises(CorruptDataError):
            migrate({"schema_version": 999})


class TestProfiles:
    def test_create_and_list(self, store: ProfileStore) -> None:
        assert store.list_profiles() == []
        store.create_profile("Ana")
        store.create_profile("Luis-2")
        assert store.list_profiles() == ["Ana", "Luis-2"]

    def test_duplicate_rejected(self, store: ProfileStore) -> None:
        store.create_profile("Ana")
        with pytest.raises(FileExistsError):
            store.create_profile("Ana")

    def test_empty_name_rejected(self, store: ProfileStore) -> None:
        with pytest.raises(ValueError):
            store.create_profile("///")

    def test_profiles_are_isolated(self, store: ProfileStore) -> None:
        store.create_profile("a")
        store.create_profile("b")
        store.save("a", {"history": [1]})
        store.save("b", {"history": [2, 3]})
        assert store.load("a")["history"] == [1]
        assert store.load("b")["history"] == [2, 3]

    def test_save_then_load_roundtrip(self, store: ProfileStore) -> None:
        store.create_profile("Ana")
        payload = {"settings": {"theme": "dark"}, "history": [{"net_wpm": 42.5}]}
        store.save("Ana", payload)
        assert store.load("Ana")["settings"]["theme"] == "dark"

    def test_load_recovers_corrupt_profile(self, store: ProfileStore) -> None:
        store.create_profile("Ana")
        store.save("Ana", {"settings": {"theme": "dark"}})
        store.save("Ana", {"settings": {"theme": "neon"}})
        path = store.profile_path("Ana")
        path.write_text("not json", encoding="utf-8")
        data = store.load("Ana")
        assert data["settings"]["theme"] == "dark"  # falls back to the previous good copy

    def test_load_missing_profile_raises(self, store: ProfileStore) -> None:
        with pytest.raises(FileNotFoundError):
            store.load("ghost")
