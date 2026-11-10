# F0 Audit — Repository state and legacy module decisions

Date: 2026-11-10 · Scope: full repo read at `main` (commit `eeb8c5a`), full git history (`git fetch --unshallow`, 2 branches of history, all deletes inspected).

## 1. Verified facts (confirmed by execution, not assumed)

| Claim in STATE.md / README | Reality |
|---|---|
| Theme system Light/Dark/Neon | ✅ Exists: `src/ui/themes.py` (325 lines, palettes + QSS helpers) |
| Core typing engine (WPM, accuracy, per-char state) | ✅ Exists: `src/core/engine.py` (182 lines). Pure logic, no Qt. Smoke-tested OK |
| Weak-key tracking (`src/core/weak_keys.py`) | ✅ Exists (196 lines): attempts/errors/ranking/drill generator. Smoke-tested OK |
| Responsive MainWindow + NeonFrame pulse/glow | ❌ **Does not exist**. `src/main.py:19` imports `ui.main_window` which is not in the repo |
| Virtual keyboard with finger legend | ❌ Does not exist (no file, no commit ever added it) |
| 15 progressive lessons + unlock + pass criteria | ❌ Does not exist. No `src/core/lessons.py`, no `src/data/` |
| Tests | ❌ No `tests/` directory at all |
| `src/core/typing_test.py` (timed test) | ❌ Does not exist → will be implemented per brief §7.2 |

**App boot check (evidence):**
```
QT_QPA_PLATFORM=offscreen python3 src/main.py
→ ModuleNotFoundError: No module named 'ui.main_window'
```
The commit `6496d8b` ("full redesign") only changed `README.md`, `STATE.md`, `requirements.txt` — the UI it describes was never committed. STATE.md is aspirational, not factual.

Also verified: PySide6 not pinned in requirements (only `>=6.6.0,<7.0.0`); no LICENSE file; no `pyproject.toml`; no CI; README project structure does not match reality.

## 2. Legacy root modules (CustomTkinter era) — decisions

Legend: **Port** = reuse logic (adapted, no new deps) · **Archive** = move to `legacy/` untouched · **Discard** = do not carry forward (archived anyway; nothing is deleted without a decision).

| Module | Decision | Justification |
|---|---|---|
| `keymaster.py` (38 KB) | Archive | Monolithic CustomTkinter UI of the old "Python code trainer" app; tied to ctk widgets. Reference only. |
| `splash_screen.py` | Archive | CustomTkinter + PIL. Concept (intro sequence) is reused in F6 as a PySide6 widget; code is not portable. |
| `onboarding.py` | Archive | ctk UI. New onboarding (§5.7) is 3 screens, different flow, PySide6. |
| `contracts_ui.py` | Archive | ctk UI mixin for daily contracts; revisit in F8 only if gamification is wanted. |
| `fsrs_banner.py` | Archive | ctk UI; the FSRS logic it displays lives in `fsrs.py` (ported separately). |
| `path_checklist_ui.py` | Archive | ctk UI for the old concept-path feature; out of scope for a typing tutor. |
| `profile_manager.py` | Archive | Old persistence: flat JSON in CWD, UI mixins mixed in, broad `except Exception`. Replaced by §7.3 XDG + atomic-write store. |
| `sound_engine.py` | Archive | Depends on pygame (new dependency, not justified). Sound is rewritten with stdlib `wave` + `QSoundEffect` (§5.9); its envelope/decay ideas are reused. |
| `fsrs.py` | **Port** | Pure Python, zero UI deps, FSRS-lite scheduler with D/S model and grade mapping. Fits §5.3 (spaced review of weak keys). Ported in F3/F5 with tests, trimmed to what is used. |
| `error_classifier.py` | **Port** | Pure Python; classifies typo vs case vs adjacent-key slips. Directly serves "see which keys you fail and why" (§1, §6.9). Ported with the typing core in F2. |
| `ollama_tutor.py` | Archive | Optional F8 feature (local coach). Ported behind a config flag only after F0–F7; never a hard dependency. |
| `achievements.py` | Archive | Old gamification (25 achievements for the code trainer). Re-evaluate in F8; not core to the typing mission. |
| `daily_contracts.py` | Archive | Pure logic but coupled to old profile/contracts flow; same F8 re-evaluation as achievements. |
| `tips_system.py` | Archive | 100+ tips about Python concepts, not touch typing. Out of product scope. |
| `content_generator.py` | Archive | Generates Python fill-in-the-blank challenges; not typing practice content. |
| `builder_content.py` | Archive | Exercise bank for Constructor mode (old app). Out of scope. |
| `constructor_mode.py` | Archive | Executes user Python code (AST + sandboxing) — high risk, zero value for a typing tutor. |
| `mini_lesson.py` | Archive | Dataclass + mixin for the old trainer's lessons. Replaced by the new lesson model (§5.1). |
| `test_modules.py` | Archive | Ad-hoc test script for old modules; replaced by real pytest suite. |
| `LEARNING.md`, `keymaster_profile.example.json` | Archive | Docs/example of the old app. |
| `banner.png`, `iconos.png` | Archive (`legacy/assets/`) | Old-app artwork; `Logo.png` stays (source for packaging icons, §7.7). |
| `.kombai/` | Leave untouched | Tooling artifact not owned by this project. |

Nothing is deleted: all archived files move to `legacy/` in F1 with their history preserved by git.

## 3. Salvageable assets

- `Logo.png` → icon source for `.desktop` + hicolor icons (F7).
- `fsrs.py`, `error_classifier.py` → ported (see table).
- `src/core/engine.py`, `weak_keys.py`, `src/ui/themes.py` → kept as foundation; engine gets a keystroke-level API in F2 (current API is text-diff based and cannot measure per-key latency).

## 4. Risks found in existing core (to fix in F2, not silently)

1. `engine.py` computes WPM/accuracy from a full-text diff; no per-keystroke log → cannot feed `weak_keys.keystroke_log()` or measure key latency (§5.3). New `typing_test.py` (§7.2) becomes the keystroke-level core; `engine.py` is refactored onto it or retired if fully superseded.
2. `engine.py` accuracy denominator uses `attempted = min(len(typed), len(target))`, which inflates accuracy when the user types past a wrong char; corrected errors also vanish from accuracy. The §7.2 definitions (correct keystrokes / total keystrokes) fix this.
3. `weak_keys.py` lowercases expected keys (`record_attempt`), so `A` vs `a` and Shift errors are merged — contradicts "see why you fail". Kept API, fixed behavior via the new keystroke log.
4. `requirements.txt` is unpinned and `src/main.py` hardcodes `QFont("Segoe UI")` (a Windows font) — replaced in F1/F6 with bundled OFL fonts.

## 5. Open decision requiring owner input

- No `LICENSE` file in the repo → owner must choose one (asked; blocking `pyproject.toml` license field and font bundling compliance only, not F1 code work).
