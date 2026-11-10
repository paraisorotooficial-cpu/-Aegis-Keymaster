# F0 Test plan

## Layers

1. **Core unit tests** (`tests/core/`, pytest): pure logic, no Qt.
   - `typing_test.py`: WPM gross/net, accuracy (corrected errors count), consistency (CV over 5 s intervals), validity (<5 s or <10 keystrokes → invalid), backspace, extend, abort, injected fake clock, empty input, duration boundaries (60/180/300).
   - `engine.py`: per-char states, finish detection, past-end typing.
   - `weak_keys.py`: attempts/errors/ranking, min attempts filter, latency stats, drill generation, `keystroke_log` feeding.
   - `error_classifier.py`: typo/case/adjacent/missing/extra.
   - `persistence.py`: atomic write, `.bak` recovery, corrupted file, old schema migration, simulated full disk (monkeypatched write), interrupted write; profile isolation.
   - `layouts.py` + `data/layouts/*.json`: dead keys (´ + a → á, not an error, not a keystroke), AltGr (@ on latam), us/es/latam coverage, autodetection fallbacks (mocked `setxkbmap`).
   - `lessons.py`: unlock chain, pass criteria thresholds, star margins, review drills never affect pass state.
   - `stats.py` / history: filters, CSV/JSON export round-trip, streak calculation.
   - Long session: 30 simulated minutes of keystrokes, no exceptions, bounded memory.

2. **UI smoke tests** (`tests/ui/`, `QT_QPA_PLATFORM=offscreen`): each screen instantiated, simulated key events, `widget.grab()` for screenshots; theme switching; keyboard navigation focus order.

3. **Performance checks** (`tests/perf/` or scripts): keystroke→repaint latency <16 ms (measured with `QElapsedTimer` around repaint), startup <2 s (offscreen, measured), 60 fps budget for effects at "High" with auto-degrade.

4. **Static**: `ruff check` clean; `mypy`-style type annotations in core (annotations required, checker optional).

## Coverage target

Core ≥ 85 % (`pytest --cov=src/core`). UI smoke tests are pass/fail, not coverage-driven.

## CI (GitHub Actions)

Python 3.10 and 3.12 matrix: install system Qt libs (`libgl1`, `libegl1`, `libxkbcommon0`, `libfontconfig1`), `pip install -r requirements.txt -r requirements-dev.txt`, run ruff + pytest with `QT_QPA_PLATFORM=offscreen`.
