"""Generate keyboard layout JSON data files (us, es, latam).

Run: python scripts/gen_layouts.py
Output: src/data/layouts/<name>.json
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "src" / "data" / "layouts"

# Finger indices: 0-3 left pinky/ring/middle/index, 4-7 right index/middle/ring/pinky, 8 thumb.

US_ROWS = [
    ("`1234567890-=", "~!@#$%^&*()_+", "0012334456777"),
    ("qwertyuiop[]\\", "QWERTYUIOP{}|", "0123344567777"),
    ("asdfghjkl;'", 'ASDFGHJKL:"', "01233445677"),
    ("zxcvbnm,./", "ZXCVBNM<>?", "01233445677"),
]

ES_ROWS = [
    ("º1234567890'¡", 'ª!"·$%&/()=?¿', "0012334456777"),
    ("qwertyuiop`+", "QWERTYUIOP^*", "012334456777"),
    ("asdfghjklñ´ç", "ASDFGHJKLÑ¨Ç", "012334456777"),
    ("zxcvbnm,.-", "ZXCVBNM;:_", "01233445677"),
]

LATAM_ROWS = [
    ("|1234567890'¿", '°!"#$%&/()=?¡', "0012334456777"),
    ("qwertyuiop´+", "QWERTYUIOP¨*", "012334456777"),
    ("asdfghjklñ{}", "ASDFGHJKLÑ{}", "012334456777"),
    ("zxcvbnm,.-", "ZXCVBNM;:_", "01233445677"),
]

# AltGr characters keyed by base character (None = no AltGr).
ALTGR_US: dict[str, str | None] = {}
ALTGR_ES = {"q": "@", "e": "€", "2": '"', "3": "#", "4": "~", "5": "\\", "6": "¬", "7": "|"}
ALTGR_LATAM = {
    "q": "@", "e": "€", "2": '"', "3": "#", "4": "~", "5": "\\", "6": "¬", "7": "|",
    "{": "[", "}": "]",
}


def build(name: str, rows: list[tuple[str, str, str]], altgr: dict[str, str]) -> dict:
    keys: dict[str, dict] = {}
    for row, (base, shift, fingers) in enumerate(rows):
        for col, ch in enumerate(base):
            if ch in keys:
                continue
            keys[ch] = {
                "row": row,
                "finger": int(fingers[col]),
                "shift": shift[col] if col < len(shift) else ch.upper(),
                "altgr": altgr.get(ch),
                "dead": False,
            }
    keys[" "] = {"row": 4, "finger": 8, "shift": " ", "altgr": None, "dead": False}
    return {"name": name, "keys": keys, "dead_keys": DEAD_KEYS.get(name, {})}


def add_dead(layout: dict, key: str, shift: str | None = None) -> None:
    spec = layout["keys"].setdefault(
        key, {"row": 1, "finger": 7, "shift": shift, "altgr": None, "dead": False}
    )
    spec["dead"] = True


DEAD_MAPS = {
    "´": {"a": "á", "e": "é", "i": "í", "o": "ó", "u": "ú", "y": "ý",
          "A": "Á", "E": "É", "I": "Í", "O": "Ó", "U": "Ú", "Y": "Ý"},
    "`": {"a": "à", "e": "è", "i": "ì", "o": "ò", "u": "ù",
          "A": "À", "E": "È", "I": "Ì", "O": "Ò", "U": "Ù"},
    "¨": {"a": "ä", "e": "ë", "i": "ï", "o": "ö", "u": "ü",
          "A": "Ä", "E": "Ë", "I": "Ï", "O": "Ö", "U": "Ü"},
    "^": {"a": "â", "e": "ê", "i": "î", "o": "ô", "u": "û",
          "A": "Â", "E": "Ê", "I": "Î", "O": "Ô", "U": "Û"},
    "~": {"a": "ã", "o": "õ", "n": "ñ", "A": "Ã", "O": "Õ", "N": "Ñ"},
}

DEAD_KEYS = {
    "us": {},
    "es": DEAD_MAPS,
    "latam": {"´": DEAD_MAPS["´"], "¨": DEAD_MAPS["¨"], "^": DEAD_MAPS["^"]},
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    layouts = {
        "us": build("us", US_ROWS, ALTGR_US),
        "es": build("es", ES_ROWS, ALTGR_ES),
        "latam": build("latam", LATAM_ROWS, ALTGR_LATAM),
    }
    add_dead(layouts["es"], "`", shift="^")
    add_dead(layouts["es"], "´", shift="¨")
    add_dead(layouts["latam"], "´", shift="¨")
    for name, data in layouts.items():
        path = OUT / f"{name}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path} ({len(data['keys'])} keys, {len(data['dead_keys'])} dead keys)")


if __name__ == "__main__":
    main()
