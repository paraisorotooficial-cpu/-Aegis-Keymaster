# STATE.md — Aegis Keymaster

**Last updated:** 2026-11-10 (F0 audit complete)
**Truth policy:** this file lists only code that actually exists in the repo, verified by execution. The previous version described UI modules that were never committed; that discrepancy is documented in `docs/audit-f0.md`.

## Goal
Complete, tested, documented, installable touch-typing tutor for Linux (Lubuntu 26.04, LXQt), PySide6, cyberpunk neon aesthetics (Light/Dark/Neon), following the phased plan F0–F8.

## Confirmed current state (verified)
- `src/core/engine.py` — typing engine (text-diff based; needs keystroke-level rework in F2). Smoke-tested.
- `src/core/weak_keys.py` — weak-key tracker + drill generator. Smoke-tested.
- `src/ui/themes.py` — Light/Dark/Neon palettes + QSS helpers.
- `src/main.py` — entry point; **currently broken**: imports `ui.main_window` which does not exist (verified: `ModuleNotFoundError: No module named 'ui.main_window'`).
- Root contains 19 legacy CustomTkinter modules; audit and decisions in `docs/audit-f0.md` (port: `fsrs.py`, `error_classifier.py`; archive: rest; nothing deleted).

## Decisions taken
- STATE.md/README claims vs reality discrepancy resolved by rebuilding missing UI from scratch per brief (no files were ever lost — full git history checked).
- Design plan fixed: `docs/design-plan.md` (neon rationed to typing line only; Inter + JetBrains Mono, OFL).
- Test plan fixed: `docs/test-plan.md`.
- PySide6 pinned `==6.8.3` for dev; requirements will be exact-pinned in F1.

## Phase status
- F0 Auditoría y diseño — **Verificada** (audit + design plan + test plan delivered; app boot failure at HEAD reproduced and documented).
- F1 Base técnica — **Verificada**: `legacy/` created (21 files archived, nothing deleted), `pyproject.toml` + pinned `requirements.txt` + `requirements-dev.txt`, ruff clean, logging, working MainWindow shell with theme switching, `src/app.py` factory, CI workflow, app boots offscreen.
- F2 Test cronometrado — **Verificada**:
  - Core: `src/core/typing_test.py` (brief §7.2 complete: durations 60/180/300, injectable clock, timer starts on first keystroke, non-blocking errors + backspace, extend/abort, gross/net WPM, keystroke accuracy, consistency via CV of 5 s intervals, validity <5 s or <10 keystrokes, `TestResult.to_dict()`, `key_stats()` with latency, `keystroke_log()`).
  - Core: `src/core/error_classifier.py` ported from legacy (case/adjacent/other).
  - Core: `weak_keys.py` gained latency fields + `ingest_log()`.
  - Data: `src/data/test_texts.json` (es/en) + `src/core/test_texts.py` loader.
  - UI: `src/ui/typing_area.py` (QPainter typing line, cached layout, dim/correct/error+underline, cyan cursor), `src/ui/test_mode.py` (setup → live → report flow, IntervalChart), MainWindow navigation wired.
  - Evidence: 84 tests green (0 warnings), core coverage 92 %, keystroke→repaint p95 < 1 ms offscreen (budget 16 ms), boot OK offscreen.
- F3 Persistencia y perfiles — Pendiente (next).
- F4 Estadísticas — Pendiente.
- F5 Curso completo y distribuciones — Pendiente.
- F6 Pulido — Pendiente.
- F7 Entrega — Pendiente.
- F8 Opcionales — Pendiente.

## F2 notes / declared assumptions
- Best-record comparison ("vs. mejor marca") is per-app-session until F3 persistence lands.
- "Repasar teclas débiles" currently feeds the weak-key tracker from the test's keystroke log and generates a drill; the drill plays inside the course screen in F5.
- Live WPM uses net WPM (correct chars on screen), matching §7.2 definitions.
- Dead keys / AltGr composition land in F5 with the layout layer; the typing area currently receives composed characters from Qt input events, which handles dead keys on real X11 sessions.

## Bugs fixed in F1 (found by tests, cause diagnosed first)
- `engine.py`: `_finished` was sticky after backspace (window lost its CURRENT char; computed after the state loop but read inside it). Now recomputed before the loop.
- `weak_keys.py`: expected keys were lowercased, merging `A`/`a` and hiding Shift errors. Case is now preserved.

## Open questions
- LICENSE file missing → owner asked (timeout, will re-ask); `pyproject.toml` currently declares `Proprietary` as a declared assumption, trivially changeable.

## Next step
F3: persistence (§7.3) — XDG data home, atomic writes with .bak recovery, schema_version + migrations, per-profile folders; corrupt/old-version/full-disk/interrupted-write tests; settings screen; wire test results and lesson progress into the store.
