"""Performance budget measurements (offscreen).

Run: QT_QPA_PLATFORM=offscreen python scripts/benchmark.py

Budgets (brief §4):
- boot to usable window < 2 s
- keystroke -> repaint < 16 ms
- RAM (normal use) < 250 MB
"""

from __future__ import annotations

import resource
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QTimer
from PySide6.QtTest import QTest
from src.app import App


def measure_boot(app: App) -> float:
    started = time.perf_counter()
    shown = {"at": None}

    def on_shown() -> None:
        shown["at"] = time.perf_counter()

    app.window.show()
    QTimer.singleShot(0, on_shown)
    app.qt_app.processEvents()
    return (shown["at"] or time.perf_counter()) - started


def measure_keystroke_latency(app: App, strokes: int = 200) -> list[float]:
    page = app.window.course_page
    page._open_lesson("L01")
    screen = page.lesson_screen
    samples: list[float] = []
    screen._typing_area.set_frame_listener(samples.append)
    text = screen._text[:strokes]
    for char in text:
        QTest.keyClicks(screen._typing_area, char)
        app.qt_app.processEvents()
    return samples


def main() -> int:
    app = App(sys.argv)
    boot = measure_boot(app)
    samples = measure_keystroke_latency(app)
    ram_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024

    print(f"boot_to_window:      {boot * 1000:8.1f} ms   (budget 2000 ms)")
    print(f"keystroke_repaints:  {len(samples):8d} samples")
    p95 = 0.0
    if samples:
        p95 = statistics.quantiles(samples, n=20)[-1]
        print(f"  mean:              {statistics.mean(samples) * 1000:8.2f} ms")
        print(f"  p95:               {p95 * 1000:8.2f} ms   (budget 16 ms)")
        print(f"  max:               {max(samples) * 1000:8.2f} ms")
    print(f"ram_peak:            {ram_mb:8.1f} MB   (budget 250 MB)")

    ok = boot < 2.0 and (not samples or p95 < 0.016) and ram_mb < 250
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
