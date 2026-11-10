"""Keyboard layout data layer: loading, detection, lookup and dead-key composition."""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from functools import cache
from importlib import resources

log = logging.getLogger(__name__)


class LayoutError(Exception):
    """Raised when a layout cannot be loaded or is malformed."""


@dataclass(frozen=True)
class KeySpec:
    char: str
    row: int
    finger: int
    shift: str
    altgr: str | None
    dead: bool


@dataclass(frozen=True)
class KeyPlacement:
    """Where a character lives on the physical keyboard."""

    base: str
    needs_shift: bool
    needs_altgr: bool
    spec: KeySpec


class KeyboardLayout:
    """Immutable view over a layout JSON file."""

    def __init__(
        self, name: str, keys: dict[str, KeySpec], dead_keys: dict[str, dict[str, str]]
    ) -> None:
        self.name = name
        self._keys = keys
        self.dead_keys = dead_keys
        self._reverse: dict[str, KeyPlacement] = {}
        for base, spec in keys.items():
            if spec.shift and spec.shift not in self._reverse:
                self._reverse[spec.shift] = KeyPlacement(base, True, False, spec)
            if spec.altgr and spec.altgr not in self._reverse:
                self._reverse[spec.altgr] = KeyPlacement(base, False, True, spec)
            if base not in self._reverse:
                self._reverse[base] = KeyPlacement(base, False, False, spec)

    @property
    def keys(self) -> dict[str, KeySpec]:
        return dict(self._keys)

    def spec(self, char: str) -> KeySpec | None:
        return self._keys.get(char)

    def placement(self, char: str) -> KeyPlacement | None:
        return self._reverse.get(char)

    def compose(self, dead: str, following: str) -> str | None:
        """Return the composed character for a dead key + base char, or None."""
        table = self.dead_keys.get(dead)
        if table is None:
            return None
        return table.get(following) or table.get(following.lower())

    def composable(self, char: str) -> bool:
        """True if the character can be produced by a dead-key composition."""
        return any(char in table.values() for table in self.dead_keys.values())

    def composition(self, char: str) -> tuple[str, str] | None:
        """Return (dead_key, base_char) that composes into char, or None."""
        for dead, table in self.dead_keys.items():
            for base, composed in table.items():
                if composed == char:
                    return dead, base
        return None

    def can_type(self, char: str) -> bool:
        """True if the character is typeable on this layout (direct or composed)."""
        return self.spec(char) is not None or self.composable(char)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "dead_keys": self.dead_keys,
            "keys": {
                char: {
                    "row": s.row,
                    "finger": s.finger,
                    "shift": s.shift,
                    "altgr": s.altgr,
                    "dead": s.dead,
                }
                for char, s in self._keys.items()
            },
        }


def _parse(data: dict) -> KeyboardLayout:
    try:
        name = data["name"]
        raw_keys = data["keys"]
        dead = data.get("dead_keys", {})
        keys = {
            char: KeySpec(char, int(k["row"]), int(k["finger"]), k.get("shift", char),
                          k.get("altgr"), bool(k.get("dead", False)))
            for char, k in raw_keys.items()
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise LayoutError(f"malformed layout data: {exc}") from exc
    if " " not in keys:
        raise LayoutError("layout is missing the space key")
    return KeyboardLayout(name, keys, dead)


@cache
def load_layout(name: str) -> KeyboardLayout:
    """Load a layout by name from src/data/layouts/<name>.json."""
    if not name or "/" in name or ".." in name or name.startswith("."):
        raise LayoutError(f"invalid layout name: {name!r}")
    try:
        text = (resources.files("src.data.layouts") / f"{name}.json").read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise LayoutError(f"layout not found: {name}") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LayoutError(f"layout {name} is not valid JSON: {exc}") from exc
    return _parse(data)


def available_layouts() -> list[str]:
    try:
        return sorted(
            p.stem for p in resources.files("src.data.layouts").iterdir() if p.suffix == ".json"
        )
    except (FileNotFoundError, NotADirectoryError):
        return ["us"]


def detect_layout() -> str:
    """Best-effort keyboard layout detection; falls back to 'us'."""
    known = set(available_layouts())
    for command in (
        ["setxkbmap", "-query"],
        ["localectl", "status"],
    ):
        try:
            out = subprocess.run(command, capture_output=True, text=True, timeout=2, check=False)
        except (OSError, subprocess.SubprocessError):
            continue
        if out.returncode != 0:
            continue
        for line in out.stdout.splitlines():
            line = line.strip()
            if line.startswith("layout:") or line.startswith("X11 Layout:"):
                codes = line.split(":", 1)[1].split()
                for code in codes:
                    if code in known:
                        return code
    return "us"
