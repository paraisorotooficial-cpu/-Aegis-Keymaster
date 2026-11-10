"""Error classification for KeyMaster — Phase 2.3.

Categories:
  typo       — single-char / adjacent-key slip
  case       — wrong capitalization
  missing    — user stopped short / omitted chars
  extra      — typed beyond target or inserted chars
  syntax     — invalid Python (Constructor)
  semantic   — runs but fails tests / wrong answer token
  concept    — first tokens diverge a lot (likely misunderstanding)
  other
"""
from __future__ import annotations
from typing import Any, Dict, Optional, Tuple


_NEIGHBORS = {
    "a": "sqwz", "b": "vghn", "c": "xdfv", "d": "serfcx", "e": "wrsdf",
    "f": "drtgvc", "g": "ftyhbv", "h": "gyujnb", "i": "ujklo", "j": "huiknm",
    "k": "jiolm", "l": "kop", "m": "njk", "n": "bhjm", "o": "iklp",
    "p": "ol", "q": "wa", "r": "edft", "s": "awedxz", "t": "rfgy",
    "u": "yhji", "v": "cfgb", "w": "qase", "x": "zsdc", "y": "tghu",
    "z": "asx",
    "0": "9", "1": "2", "2": "13", "3": "24", "4": "35", "5": "46",
    "6": "57", "7": "68", "8": "79", "9": "80",
}


def _is_adjacent(a: str, b: str) -> bool:
    if not a or not b:
        return False
    a, b = a.lower(), b.lower()
    return b in _NEIGHBORS.get(a, "") or a in _NEIGHBORS.get(b, "")


def classify_typing_error(user: str, target: str) -> Dict[str, Any]:
    user = user or ""
    target = target or ""
    if user == target:
        return {"category": "none", "message": "", "position": -1, "expected": "", "got": ""}

    n = min(len(user), len(target))
    i = 0
    while i < n and user[i] == target[i]:
        i += 1

    if len(user) < len(target) and i == len(user):
        return {
            "category": "missing",
            "message": f"Falta codigo · esperaba continuar con {target[i:i+8]!r}",
            "position": i,
            "expected": target[i : i + 1] if i < len(target) else "",
            "got": "",
        }

    if len(user) > len(target) and i == len(target):
        return {
            "category": "extra",
            "message": f"Caracteres de mas al final: {user[i:]!r}",
            "position": i,
            "expected": "",
            "got": user[i : i + 1],
        }

    exp = target[i] if i < len(target) else ""
    got = user[i] if i < len(user) else ""

    if exp and got and exp.lower() == got.lower() and exp != got:
        return {
            "category": "case",
            "message": f"Mayusculas · esperaba {exp!r}, escribiste {got!r}",
            "position": i,
            "expected": exp,
            "got": got,
        }

    if exp and got and abs(len(user) - len(target)) <= 1:
        if _is_adjacent(exp, got) or (len(user) == len(target)):
            diffs = sum(1 for a, b in zip(user, target) if a != b) + abs(len(user) - len(target))
            if diffs <= 2:
                return {
                    "category": "typo",
                    "message": f"Posible typo · {got!r} en vez de {exp!r} (pos {i + 1})",
                    "position": i,
                    "expected": exp,
                    "got": got,
                }

    if i <= max(2, len(target) // 5):
        return {
            "category": "concept",
            "message": f"Patron distinto · esperaba empezar con {target[:min(12, len(target))]!r}",
            "position": i,
            "expected": exp,
            "got": got,
        }

    return {
        "category": "semantic",
        "message": f"Desvio en pos {i + 1} · esperaba {exp!r}, got {got!r}",
        "position": i,
        "expected": exp,
        "got": got,
    }


def classify_constructor_error(
    user_code: str = "",
    target_code: str = "",
    syntax_error: Optional[BaseException] = None,
    test_error: Optional[BaseException] = None,
    test_message: str = "",
) -> Dict[str, Any]:
    if syntax_error is not None:
        msg = str(syntax_error)
        return {
            "category": "syntax",
            "message": f"Sintaxis · {type(syntax_error).__name__}: {msg[:120]}",
            "position": getattr(syntax_error, "lineno", None),
            "expected": "",
            "got": "",
        }
    if test_error is not None or test_message:
        name = type(test_error).__name__ if test_error else "Assert"
        detail = test_message or str(test_error or "")
        cat = "semantic"
        low = (name + " " + detail).lower()
        if "nameerror" in low or "typeerror" in low:
            cat = "concept"
        return {
            "category": cat,
            "message": f"Test · {name}: {detail[:140]}",
            "position": -1,
            "expected": "",
            "got": "",
        }
    if user_code is not None and target_code is not None:
        u = (user_code or "").strip()
        t = (target_code or "").strip()
        if u != t:
            info = classify_typing_error(u, t)
            if info["category"] == "none":
                info = {
                    "category": "semantic",
                    "message": "Codigo distinto al esperado",
                    "position": -1,
                    "expected": "",
                    "got": "",
                }
            return info
    return {
        "category": "other",
        "message": "Error no clasificado",
        "position": -1,
        "expected": "",
        "got": "",
    }


CATEGORY_LABELS = {
    "typo": ("Typo", "#FFB020"),
    "case": ("Mayusculas", "#A855F7"),
    "missing": ("Falta texto", "#00E5FF"),
    "extra": ("Extra", "#FFB020"),
    "syntax": ("Sintaxis", "#FF3355"),
    "semantic": ("Semantica", "#FF2BD6"),
    "concept": ("Concepto", "#FF3355"),
    "other": ("Otro", "#6B7C93"),
    "none": ("OK", "#39FF14"),
}


def format_feedback(info: Dict[str, Any]) -> Tuple[str, str]:
    cat = info.get("category", "other")
    label, color = CATEGORY_LABELS.get(cat, CATEGORY_LABELS["other"])
    msg = info.get("message") or label
    return f"⚠ {label}: {msg}", color
