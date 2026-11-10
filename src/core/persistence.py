"""Profile persistence — atomic, versioned, self-recovering (brief §7.3).

Layout under the XDG data home (default ``~/.local/share/aegis-keymaster``):

    profiles/<name>/profile.json      current data
    profiles/<name>/profile.json.bak  previous good copy

Rules:
- Writes are atomic: temp file in the same directory + fsync + os.replace.
- The previous good file is kept as ``.bak`` before every replace.
- A corrupted main file is recovered from ``.bak`` automatically.
- User data is never deleted: if both files are unreadable, raise.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1
APP_DIR_NAME = "aegis-keymaster"
PROFILES_DIR_NAME = "profiles"

MIGRATIONS: dict[int, Callable[[dict[str, Any]], dict[str, Any]]] = {}


class StorageError(OSError):
    """A save operation failed; existing data is untouched."""


class CorruptDataError(ValueError):
    """Neither the main file nor the backup could be read."""


def default_data_home() -> Path:
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / APP_DIR_NAME


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    """Write JSON atomically: temp file, fsync, replace. Keeps a .bak copy."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    bak = path.with_suffix(path.suffix + ".bak")
    try:
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists():
            shutil.copyfile(path, bak)
        os.replace(tmp, path)
    except OSError as exc:
        tmp.unlink(missing_ok=True)
        raise StorageError(f"could not write {path}: {exc}") from exc


def read_json_with_recovery(path: Path) -> tuple[dict[str, Any], bool]:
    """Read a JSON file, falling back to the .bak copy. Returns (data, recovered)."""
    for target, recovered in ((path, False), (path.with_suffix(path.suffix + ".bak"), True)):
        if not target.exists():
            continue
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
            logger.warning("Unreadable %s: %s", target, exc)
            continue
        if not isinstance(data, dict):
            logger.warning("Unexpected content in %s: not an object", target)
            continue
        return data, recovered
    if path.exists() or path.with_suffix(path.suffix + ".bak").exists():
        raise CorruptDataError(f"both {path} and its backup are unreadable")
    raise FileNotFoundError(f"no profile data at {path}")


def migrate(data: dict[str, Any]) -> dict[str, Any]:
    """Bring a data dict up to SCHEMA_VERSION by applying chained migrations."""
    version = int(data.get("schema_version", 0))
    if version > SCHEMA_VERSION:
        raise CorruptDataError(
            f"data schema v{version} is newer than supported v{SCHEMA_VERSION}"
        )
    while version < SCHEMA_VERSION:
        step = MIGRATIONS.get(version)
        if step is None:
            logger.warning("No migration from v%s; assuming current schema", version)
            version = SCHEMA_VERSION
            data["schema_version"] = SCHEMA_VERSION
            break
        data = step(data)
        version = int(data.get("schema_version", version + 1))
    return data


class ProfileStore:
    """Creates, lists, loads and saves per-profile data folders."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or default_data_home()
        self.profiles_dir = self.base_dir / PROFILES_DIR_NAME

    def list_profiles(self) -> list[str]:
        if not self.profiles_dir.exists():
            return []
        return sorted(
            entry.name
            for entry in self.profiles_dir.iterdir()
            if entry.is_dir() and (entry / "profile.json").exists()
        )

    def create_profile(self, name: str) -> Path:
        safe = _safe_name(name)
        folder = self.profiles_dir / safe
        if folder.exists():
            raise FileExistsError(f"profile {name!r} already exists")
        folder.mkdir(parents=True)
        atomic_write_json(
            folder / "profile.json",
            {"schema_version": SCHEMA_VERSION, "name": name},
        )
        return folder

    def profile_path(self, name: str) -> Path:
        return self.profiles_dir / _safe_name(name) / "profile.json"

    def load(self, name: str) -> dict[str, Any]:
        data, recovered = read_json_with_recovery(self.profile_path(name))
        if recovered:
            logger.warning("Profile %s recovered from backup", name)
        data = migrate(data)
        data.setdefault("name", name)
        return data

    def save(self, name: str, data: dict[str, Any]) -> None:
        payload = dict(data)
        payload["schema_version"] = SCHEMA_VERSION
        atomic_write_json(self.profile_path(name), payload)


def _safe_name(name: str) -> str:
    safe = "".join(ch for ch in name if ch.isalnum() or ch in "-_ ").strip()
    if not safe:
        raise ValueError("profile name cannot be empty")
    return safe
