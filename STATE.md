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
- F3 Persistencia y perfiles — **Verificada**:
  - Core: `src/core/persistence.py` (atomic writes temp+fsync+replace, `.bak` of the previous good copy, recovery from `.bak` on corruption, `CorruptDataError` when both are unreadable — user data never deleted, `schema_version` + migration chain, `ProfileStore` with per-profile folders).
  - Core: `src/core/user_data.py` (`UserData`: settings with defaults, valid-only test history, `best_for(duration)`, `total_practice_seconds`), `src/core/typing_test.py` results recorded via `record_test`.
  - UI: `src/ui/settings_screen.py` (theme, effects level, reduce motion, font size, sound volume/enable, error mode, cursor style, virtual keyboard toggle, layout, UI language, CSV/JSON export, profile selector + create).
  - App wiring: `src/app.py` loads/creates the `default` profile under XDG data home, applies persisted theme, saves on every settings change, on each valid test completion and on close; profile switching isolates data.
  - Evidence: 121 tests green; persistence coverage 93 %; end-to-end check with real App: theme survives restart, invalid tests excluded, `.bak` present.
- F4 Estadísticas — **Verificada**:
  - Core: `src/core/stats.py` (moving averages, WPM/accuracy trends, records per duration, day streak, history filters by mode/duration/day, heatmap data with error rate + latency).
  - Core: `src/core/export.py` (CSV/JSON export, shared with settings).
  - Persistence: `UserData.record_test` stamps timestamp + mode; `App._update_weak_keys` accumulates per-key stats into `weak_key_stats` and saves.
  - UI: `src/ui/progress_screen.py` — summary (streak/practice time/valid tests), WPM + accuracy trend charts, keyboard heatmap with error/latency toggle, history table with filters; refresh on navigation and after each valid test.
  - Evidence: 149 tests green; core coverage 93 % (stats 97 %, export 100 %); E2E: a saved test appears in table, heatmap and summary numbers match the data.
- F5 Curso completo y distribuciones — **Verificada**:
  - Data: `src/data/layouts/{us,es,latam}.json` (finger/shift/altgr/dead per key, generated by `scripts/gen_layouts.py`), `src/data/lessons.json` (15 lessons, criteria 15→35 WPM, 90→95 %), `src/data/words_es.json` (350 words).
  - Core: `src/core/layouts.py` (load/reverse lookup/compose/autodetect), `src/core/lessons.py` (unlock chain, stars 1/2/3 at +20 %/+40 %, text generation restricted to unlocked keys with drill fallback), `WeakKeyTracker.from_dict`.
  - UI: `src/ui/virtual_keyboard.py` (data-driven, next-key + Shift/AltGr/dead highlight, amber weak keys), `src/ui/course_mode.py` (list with locks/stars, lesson screen, reviews never affect pass), `src/ui/onboarding.py` (3 skippable screens: language+layout, 1-min placement test, recommendation), `src/ui/layouts_combo.py`.
  - Typing path: dead keys swallowed and composed in `TypingArea` (á counts, ´ alone does not); AltGr chars typed directly.
  - App: lesson results persist in `lesson_progress`, drills feed `weak_key_stats`, layout setting propagates everywhere, onboarding runs once.
  - Evidence: 193 tests green; explicit á/ñ/¿/¡/@ cases; E2E offscreen L01 → 3 stars + weak keys + saved profile.
- F6 Pulido — **Verificada**:
  - Sound: `src/core/sound.py` (synthesized WAVs, cached under XDG), `src/ui/sound_player.py` (QSoundEffect, volume/mute/disable, silent no-op without libpulse). Key + error sounds on every keystroke in lesson and test screens; pass sound on lesson completion; test-end sound on test completion; all wired through settings.
  - Effects: `src/ui/effects.py` levels high/medium/low/off (cursor glide 90/60/0/0 ms, glow 1.0/0.6/0.25/0.0) + `EffectsController` auto-downgrade at <45 fps over 5 s (once). Applied to lesson and test typing areas; `reduce_motion` forces instant cursor.
  - Accessibility: focus styles (2 px cyan) for buttons/combos/checkboxes in `themes.py`; underline on errors (color + shape) already in TypingArea.
  - i18n: `src/core/i18n.py` es/en tables; nav retranslates live, screens at rebuild (declared limitation).
  - Contrast: `src/ui/contrast.py` + `scripts/check_contrast.py`; palettes fixed (text_muted) to pass AA on all 27 pairs.
  - Budgets: `scripts/benchmark.py` → boot 9.1 ms, repaint p95 1.71 ms, RAM 68 MB (all PASS, `docs/performance.md`).
- F7 Entrega — **Verificada**:
  - Versioning: `src/__version__.py` (`1.0.0`) is the single source; `pyproject.toml` reads it via `setuptools.dynamic`, `App` sets `applicationVersion`.
  - Packaging: `packaging/aegis-keymaster.desktop`, `install.sh` (user install to `~/.local` via pip, hicolor icons, desktop entry, `--uninstall` keeps user data), icons generated from Logo.png at 16–256 px (`scripts/gen_icons.py`, `assets/icons/`).
  - Fonts: DejaVu Sans + DejaVu Sans Mono (regular + bold) bundled in `src/assets/fonts/` with `LICENSE-DejaVu.txt`; loaded via `QFontDatabase.addApplicationFont` (`src/ui/fonts.py`); cover á é í ó ú ü ñ ¿ ¡ (verified by rendering).
  - README rewritten with screenshots, install/uninstall, shortcuts, structure, measured budgets.
  - Screenshot pipeline: `scripts/capture_screens.py` → `docs/screenshots/{course,test-live,test-report,progress,settings}.png`, OCR-verified readable.
  - Font fix (root cause found): the app font was never applied (`apply_application_font` existed but was never called) and QSS `font-size` rules break glyph rendering under broken fontconfig (tofu). Fix: app font applied at startup and on `font_size` setting change; font sizes for Title/Subtitle moved from QSS to explicit `QFont` helpers (`title_font()`/`subtitle_font()`); `font-weight` in QSS verified safe.
  - Esc now aborts the running test (`TestLiveScreen.keyPressEvent`) and exits the lesson (`LessonScreen.keyPressEvent`), matching the README shortcut table.
  - Long-session test: `tests/ui/test_long_session.py` — 30 simulated minutes (30 × 60 s engine sessions ≈ 9000 keystrokes) plus 1800 keystrokes through the live widget with tracemalloc checks; no exceptions, bounded memory.
  - Clean-install test: `pip install --no-deps --prefix /tmp/f7-test .` → layouts JSONs, fonts TTFs and the `aegis-keymaster` entry point land in the installed tree; entry point boots offscreen from site-packages and creates `profiles/` + `logs/` under XDG data home.
  - Evidence: 208 tests green, ruff clean, WCAG AA pass (27/27), benchmark PASS (boot 8.6 ms, repaint p95 2.09 ms, RAM 69 MB), core coverage 94 %.
- F8 Opcionales — Pendiente (declared not done; see Open questions).

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
F8 optionals (falling-words minigame, Ollama coach, achievements/daily contracts — all behind config flags) were not implemented; everything in F0–F7 is verified. Optional follow-ups: .deb packaging (optional per brief), LICENSE decision, sound verification on real PulseAudio hardware.

## Sandbox limitations (declared, not app bugs)
- No libpulse → sounds verified as synthesized WAV bytes + graceful degradation only.
- Broken fontconfig → screenshots captured with bundled fonts; QSS `font-size` rules removed because they trigger tofu under broken fontconfig (on real systems they would be harmless, but bundled-font-first is more robust).
- No display → all UI verification offscreen via `widget.grab()` + OCR of captures.
