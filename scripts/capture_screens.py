"""Capture screenshots of every main screen (offscreen) for the README.

Run: QT_QPA_PLATFORM=offscreen python scripts/capture_screens.py
Output: docs/screenshots/*.png
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.app import App

OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"


def capture(app: App, name: str, prepare=None) -> None:
    if prepare is not None:
        prepare(app)
    app.qt_app.processEvents()
    pixmap = app.window.grab()
    path = OUT / f"{name}.png"
    if not pixmap.save(str(path), "PNG"):
        print(f"failed to save {path}", file=sys.stderr)
        return
    print(f"wrote {path}")


def open_lesson(app: App) -> None:
    app.window.navigate(0)
    app.window.course_page._open_lesson("L01")


def open_test_live(app: App) -> None:
    app.window.navigate(1)
    app.window.test_page._on_start(60, "es")


def open_report(app: App) -> None:
    app.window.navigate(1)
    app.window.test_page._on_start(60, "es")
    page = app.window.test_page
    session = page._live._session
    assert session is not None
    for char in session.text[:120]:
        session.type_char(char)
    page._on_finished(session.result(), session.key_stats())


def open_progress(app: App) -> None:
    app.window.navigate(2)


def open_settings(app: App) -> None:
    app.window.navigate(3)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    app = App(sys.argv)
    app.window.show()
    capture(app, "course", open_lesson)
    capture(app, "test-live", open_test_live)
    capture(app, "test-report", open_report)
    capture(app, "progress", open_progress)
    capture(app, "settings", open_settings)
    return 0


if __name__ == "__main__":
    sys.exit(main())
