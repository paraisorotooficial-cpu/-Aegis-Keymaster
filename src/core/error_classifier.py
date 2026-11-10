"""Classify a single typing error: why the pressed key was wrong.

Ported from the legacy ``error_classifier.py`` (F0 audit), trimmed to what a
typing tutor needs: case slips, adjacent-key slips and other typos.
"""

from __future__ import annotations

from dataclasses import dataclass

CATEGORIES = ("none", "case", "adjacent", "other")

_NEIGHBORS: dict[str, str] = {
    "a": "sqwz", "b": "vghn", "c": "xdfv", "d": "serfcx", "e": "wrsdf",
    "f": "drtgvc", "g": "ftyhbv", "h": "gyujnb", "i": "ujklo", "j": "huiknm",
    "k": "jiolm", "l": "kopñ", "m": "njk", "n": "bhjm", "o": "iklp",
    "p": "ol", "q": "wa", "r": "edft", "s": "awedxz", "t": "rfgy",
    "u": "yhji", "v": "cfgb", "w": "qase", "x": "zsdc", "y": "tghu",
    "z": "asx", "ñ": "lmk",
    "0": "9", "1": "2", "2": "13", "3": "24", "4": "35", "5": "46",
    "6": "57", "7": "68", "8": "79", "9": "80",
    ",": "m.", ".": ",-", "-": ".0", "'": "ñ;", "´": "´+",  # noqa: RUF001
}


@dataclass(frozen=True)
class ErrorInfo:
    """Why one keystroke was wrong."""

    category: str
    expected: str
    typed: str
    adjacent: bool

    @property
    def is_error(self) -> bool:
        return self.category != "none"


def classify_keystroke(expected: str, typed: str) -> ErrorInfo:
    """Classify one wrong keystroke.

    ``none`` when correct; ``case`` for a Shift slip; ``adjacent`` when the
    pressed key neighbours the expected one; ``other`` otherwise.
    """
    if typed == expected:
        return ErrorInfo("none", expected, typed, adjacent=False)
    if expected and typed and typed.lower() == expected.lower():
        return ErrorInfo("case", expected, typed, adjacent=False)
    if _is_adjacent(expected, typed):
        return ErrorInfo("adjacent", expected, typed, adjacent=True)
    return ErrorInfo("other", expected, typed, adjacent=False)


def _is_adjacent(expected: str, typed: str) -> bool:
    if not expected or not typed or len(expected) != 1 or len(typed) != 1:
        return False
    a, b = expected.lower(), typed.lower()
    return b in _NEIGHBORS.get(a, "") or a in _NEIGHBORS.get(b, "")
