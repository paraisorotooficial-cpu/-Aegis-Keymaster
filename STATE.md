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
- F1 Base técnica — **Verificada**: `legacy/` created (21 files archived, nothing deleted), `pyproject.toml` + pinned `requirements.txt` + `requirements-dev.txt`, ruff clean, logging (`src/utils/logging_setup.py`), working MainWindow shell (`src/ui/main_window.py`) with theme switching, `src/app.py` factory, CI workflow, 24 tests green, core coverage 88 %, app boots offscreen (`python -m src.main` → "Main window shown").
- F2 Test cronometrado — Pendiente (next).
- F3 Persistencia y perfiles — Pendiente.
- F4 Estadísticas — Pendiente.
- F5 Curso completo y distribuciones — Pendiente.
- F6 Pulido — Pendiente.
- F7 Entrega — Pendiente.
- F8 Opcionales — Pendiente.

## Bugs fixed in F1 (found by tests, cause diagnosed first)
- `engine.py`: `_finished` was sticky after backspace (window lost its CURRENT char; computed after the state loop but read inside it). Now recomputed before the loop.
- `weak_keys.py`: expected keys were lowercased, merging `A`/`a` and hiding Shift errors. Case is now preserved.

## Open questions
- LICENSE file missing → owner asked (timeout, will re-ask); `pyproject.toml` currently declares `Proprietary` as a declared assumption, trivially changeable.

## Next step
F2: implement `src/core/typing_test.py` per brief §7.2 (keystroke-level session, injectable clock, validity rules), port `error_classifier.py` into `src/core/`, build test selector + live test screen + report screen, wire weak keys with latency stats.
