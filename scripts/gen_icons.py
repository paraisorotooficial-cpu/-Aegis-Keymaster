"""Generate application icons in multiple sizes from Logo.png (Qt-based, no PIL).

Run: QT_QPA_PLATFORM=offscreen python scripts/gen_icons.py
Output: assets/icons/<size>/aegis-keymaster.png
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "Logo.png"
SIZES = (16, 32, 48, 64, 128, 256)


def main() -> int:
    source = QImage(str(LOGO))
    if source.isNull():
        print(f"cannot load {LOGO}", file=sys.stderr)
        return 1
    for size in SIZES:
        out_dir = ROOT / "assets" / "icons" / str(size)
        out_dir.mkdir(parents=True, exist_ok=True)
        scaled = source.scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        path = out_dir / "aegis-keymaster.png"
        if not scaled.save(str(path), "PNG"):
            print(f"failed to save {path}", file=sys.stderr)
            return 1
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
