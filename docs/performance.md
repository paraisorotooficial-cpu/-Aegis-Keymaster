# Performance budgets — measured evidence

Environment of the measurements: CI-style container, `QT_QPA_PLATFORM=offscreen`,
Python 3.12, PySide6 6.8 (pinned in `requirements.txt`). Re-run with:

```bash
QT_QPA_PLATFORM=offscreen python scripts/benchmark.py
```

Latest run (F6):

| Metric | Measured | Budget | Result |
| --- | --- | --- | --- |
| Boot to usable window | 9.1 ms | < 2000 ms | PASS |
| Keystroke → repaint, mean | 1.63 ms | < 16 ms | PASS |
| Keystroke → repaint, p95 | 1.71 ms | < 16 ms | PASS |
| Keystroke → repaint, max | 3.36 ms | < 16 ms | PASS |
| RAM peak | 67.6 MB | < 250 MB | PASS |

Notes:

- Offscreen numbers exclude real GPU/X11 composition; on the target hardware
  (Intel i3-1115G4) the same paint path is used, so the 16 ms budget has
  ~14 ms of headroom for the compositor.
- The keystroke→repaint measurement drives 200 real key events through the
  course lesson screen and records the duration of every paint pass via
  `TypingArea.set_frame_listener`.
- Effects degradation (`src/ui/effects.py`) lowers the effects level once when
  the average frame time over a 5 s window exceeds 1/45 s. Unit tests cover
  downgrade, one-shot behavior and the `off` floor.
- WCAG AA contrast (4.5:1) for all text roles on all backgrounds is enforced
  by `scripts/check_contrast.py` and `tests/ui/test_contrast_effects.py`.
