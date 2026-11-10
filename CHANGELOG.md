# Changelog — Aegis Keymaster

All notable changes to the PySide6 typing tutor are documented here. Entries for the pre-redesign "KeyMaster Pro" CustomTkinter app are kept below.

## [1.0.0] — F7 Delivery (2026-11-10)

### Added
- `src/__version__.py` — single source of the version (`1.0.0`); `pyproject.toml` reads it via `setuptools.dynamic` and the app sets `applicationVersion` from it.
- `packaging/aegis-keymaster.desktop` + `install.sh` — one-command user install to `~/.local` (pip + hicolor icons + desktop entry) with `--uninstall` that keeps user data.
- `assets/icons/{16..256}/aegis-keymaster.png` generated from Logo.png by `scripts/gen_icons.py`.
- `src/assets/fonts/` — DejaVu Sans + DejaVu Sans Mono (regular + bold) bundled with `LICENSE-DejaVu.txt`; loaded with `QFontDatabase.addApplicationFont` from `src/ui/fonts.py`; verified to cover á é í ó ú ü ñ ¿ ¡.
- `scripts/capture_screens.py` + `docs/screenshots/` — offscreen captures of course, live test, report, progress and settings (OCR-verified readable).
- `tests/ui/test_long_session.py` — 30 simulated minutes of typing (engine-level with injected clock) plus 1800 keystrokes through the live widget with tracemalloc memory checks.
- Esc aborts the running test and exits the lesson, matching the README shortcuts.

### Fixed
- App font was never applied (`apply_application_font` existed but had no caller): widgets rendered with fallback fonts. Now applied at startup and when the `font_size` setting changes.
- QSS `font-size` rules break glyph rendering when fontconfig is broken (tofu boxes): sizes for Title/Subtitle moved from QSS to explicit `QFont` helpers (`title_font()`/`subtitle_font()`); `font-weight` verified safe and kept.

### Verified
- 208 tests green; ruff clean; WCAG AA 27/27 pairs; benchmark PASS (boot 8.6 ms, repaint p95 2.09 ms, RAM 69 MB); core coverage 94 %.
- Clean install test: `pip install --no-deps --prefix /tmp/f7-test .` → layouts, fonts and the `aegis-keymaster` entry point land in the installed tree; entry point boots offscreen from site-packages and creates profiles/logs under the XDG data home.

## [0.6.0] — F6 Polish (2026-11-10)

### Added
- `src/core/sound.py` — key click, error, lesson-pass and test-end sounds synthesized in code (`wave`/`struct`, no assets, no network), cached as WAV files under the XDG data home.
- `src/ui/sound_player.py` — `QSoundEffect` playback with volume/mute/disable; degrades to a silent no-op when no audio backend exists (verified in the sandbox, which has no libpulse).
- `src/ui/effects.py` — effects levels (high/medium/low/off) with cursor-glide duration and glow scaling per level; `EffectsController` auto-downgrades one level when the average frame time over 5 s exceeds 45 fps (announced once, logged).
- `src/core/i18n.py` + `src/ui/main_window.py` — simple es/en string tables; UI language follows the setting; navigation labels retranslate live.
- `scripts/check_contrast.py` + `src/ui/contrast.py` — WCAG AA audit of every text role on every background; script exits non-zero on failures.
- `scripts/benchmark.py` + `docs/performance.md` — boot time, keystroke→repaint latency and RAM measured against the §4 budgets.

### Fixed
- `text_muted` failed WCAG AA on several backgrounds in all three themes; palettes corrected (NEON `#7C90B0`, DARK `#7E8FA9`, LIGHT `#5D6B80`), now 4.78:1 or better everywhere.
- Virtual keyboard shift-labels computed negative point sizes (`QFont::setPointSizeF <= 0`); font size now derives from key height.
- App no longer crashes at import when PulseAudio/libpulse is absent; sounds disable gracefully.

### Verified
- 214 tests green; budgets: boot 9.1 ms (<2 s), repaint p95 1.71 ms (<16 ms), RAM 68 MB (<250 MB).
- Focus styles (2 px cyan border) added for buttons, combos and checkboxes.

## [0.5.0] — F5 Course and keyboard layouts (2026-11-10)

### Added
- `src/data/layouts/{us,es,latam}.json` + `scripts/gen_layouts.py` — layouts as data: row, finger, shift, AltGr and dead-key tables per key (48–50 keys each).
- `src/core/layouts.py` — layout loader with reverse lookup, dead-key composition (`compose`, `composition`, `can_type`) and autodetection via `setxkbmap -query` / `localectl status` with a `us` fallback.
- `src/data/lessons.json` + `src/data/words_es.json` + `src/core/lessons.py` — 15-lesson course (base row → top row → bottom row → Shift → digits → symbols → accents → ¿¡ñü → AltGr → flowing text), unlock chain, star ratings (pass / +20 % / +40 %) and lesson text generated only from unlocked keys with a letter-drill fallback.
- `src/ui/virtual_keyboard.py` — keyboard drawn from layout data; highlights the next key (base/Shift/AltGr/dead), amber border for weak keys, modifier hints.
- `src/ui/course_mode.py` — course list with stars and locks, lesson practice screen (live WPM/accuracy, non-blocking errors, result feedback) and review drills that never affect lesson pass.
- `src/ui/onboarding.py` + `src/ui/layouts_combo.py` — 3-screen skippable onboarding: language + layout, 1-minute placement test, recommended starting lesson.
- Dead-key and AltGr composition in `TypingArea`: a dead-key press is swallowed (never an error or keystroke); the composed character (á) counts; dead + space emits the dead char; unknown base falls back to the bare char.
- Course wiring in `src/app.py`: lesson results recorded into `lesson_progress`, keystrokes feed the weak-key tracker, layout setting propagates to every typing surface, onboarding runs on first launch.

### Verified
- 193 tests green; explicit cases for á, ñ, ¿, ¡, @ (AltGr on latam), dead + space, dead + unknown base, backspace cancelling composition.
- E2E offscreen: L01 completed through the UI → 3 stars recorded, weak-key stats updated, profile saved.

## [0.4.0] — F4 Statistics panel (2026-11-10)

### Added
- `src/core/stats.py` — moving-average WPM/accuracy trends, records per duration, practice time, day streak, history filtering (mode/duration/day), heatmap data (error rate + average latency per key).
- `src/core/export.py` — CSV/JSON export shared by settings and progress screens.
- `src/ui/progress_screen.py` — progress panel with QPainter-only charts: trend lines, keyboard heatmap (error rate / latency toggle), summary numbers, history table with filters; refreshes on navigation and after each valid test.
- Weak-key stats from every test now accumulate into the profile (`weak_key_stats`) and persist.

### Fixed
- `QColor.setLightnessF` is not available in PySide6 6.8 — heatmap colors now blend RGB channels directly (crash found by UI smoke tests).

### Verified
- 149 tests green; core coverage 93 % (stats 97 %, export 100 %).
- End-to-end: a valid test saved by the App appears in the history table, heatmap and summary; numbers match the underlying data.

## [0.3.0] — F3 Persistence and profiles (2026-11-10)

### Added
- `src/core/persistence.py` — XDG data home (`~/.local/share/aegis-keymaster/profiles/<name>/`), atomic writes (temp file + fsync + `os.replace`), automatic `.bak` of the previous good copy, recovery from `.bak` when the main file is corrupted, `CorruptDataError` when both are unreadable (user data is never deleted), `schema_version` with a migration chain, `ProfileStore` API.
- `src/core/user_data.py` — `UserData` model: settings with defaults (theme, effects, reduce motion, volume, sound, layout, UI language, font size, cursor style, error mode, virtual keyboard), test history (valid tests only), lesson-progress and weak-key slots for F4/F5, `best_for(duration)`, practice-time total.
- `src/ui/settings_screen.py` — settings page: appearance (theme/effects/reduce motion/font size), sound (volume/enable), typing (error mode, cursor style, virtual keyboard, layout, UI language), CSV/JSON export, profile selector and creation.
- `src/app.py` — profile lifecycle: loads or creates the `default` profile, applies the persisted theme at boot, saves on settings change, on each valid test completion and on close; profile switching isolates all data.

### Verified
- 121 tests green; persistence coverage 93 %, core total 93 %.
- Failure-mode tests: corrupted main file, both files corrupted, old schema migration, simulated full disk, interrupted write — original data intact in every case.
- End-to-end with the real App class: settings survive restart; invalid tests are never saved; `.bak` present after first save.

## [0.2.0] — F2 Timed test mode (2026-11-10)

### Added
- `src/core/typing_test.py` — timed test core per the architecture contract: allowed durations 60/180/300 s, injectable clock, timer starts on the first keystroke, non-blocking error handling with backspace, `extend`/`abort`, gross/net WPM (1 word = 5 chars), keystroke-level accuracy, consistency (100 − CV of 5 s interval speed), validity (<5 s or <10 keystrokes → invalid, never saved), JSON-serializable `TestResult`, per-key stats with latency, `keystroke_log()`.
- `src/core/error_classifier.py` — ported from legacy; classifies each wrong keystroke as case slip, adjacent-key slip or other.
- `src/core/weak_keys.py` — per-key latency tracking and `ingest_log()` so tests and lessons feed the tracker without duplicated logic.
- `src/data/test_texts.json` + `src/core/test_texts.py` — Spanish/English test texts, long enough for a 5-minute test.
- `src/ui/typing_area.py` — QPainter typing line: cached layout, dim pending / primary correct / red+underline incorrect, sliding cyan cursor (the only neon element).
- `src/ui/test_mode.py` — full test flow: duration selector (1/3/5 min) with Spanish/English text, live screen (countdown, live WPM and accuracy, abort), report screen (net/gross WPM, accuracy, consistency, 5 s interval chart, uncorrected errors, weak keys of the test, best-mark comparison, "Repasar teclas débiles" and "Repetir test"). Invalid tests show a warning and are excluded from records.
- MainWindow navigation: Curso / Test / Progreso / Ajustes buttons switch pages.

### Verified
- 84 tests green (0 warnings), core coverage 92 %.
- Keystroke→repaint p95 < 1 ms offscreen (budget: 16 ms).
- App boots offscreen with the new navigation.

## [0.1.1] — F1 Technical base (2026-11-10)

### Added
- `legacy/` — all 19 CustomTkinter-era root modules archived with justification (`legacy/README.md`, `docs/audit-f0.md`); nothing deleted.
- `pyproject.toml` — package metadata, `aegis-keymaster` entry point, ruff and pytest configuration.
- `requirements.txt` pinned to `PySide6==6.8.3`; `requirements-dev.txt` for dev tools.
- `src/app.py` — application factory with logging and theme application.
- `src/ui/main_window.py` — working main window shell: navigation bar, stacked pages, theme selector (replaces the broken import at HEAD).
- `src/utils/logging_setup.py` — stderr + optional file logging.
- `tests/core/` — engine and weak-key unit tests (24 tests, core coverage 88 %).
- `tests/ui/` — offscreen smoke tests: window boots, grabs a frame, all themes build, theme signal emits.
- `.github/workflows/ci.yml` — ruff + core tests (cov ≥ 85 %) + UI smoke on Python 3.10/3.12.

### Fixed
- `engine.py`: `_finished` stayed true after backspace, leaving the text without a current character (root cause: recomputed after the state loop that reads it).
- `weak_keys.py`: expected keys were lowercased, merging `A`/`a` and hiding Shift errors; case is now preserved.

### Verified
- `ruff check src tests` clean.
- `pytest tests` — 24 passed (offscreen for UI).
- `python -m src.main` boots offscreen and logs "Main window shown".

## [0.1.0] — F0 Audit and design (2026-11-10)

### Added
- `docs/audit-f0.md` — full repository audit: verified that the UI described in STATE.md (MainWindow, virtual keyboard, 15 lessons) was never committed; app boot failure reproduced (`ModuleNotFoundError: ui.main_window`). Decisions for all 19 legacy root modules (port: `fsrs.py`, `error_classifier.py`; archive: the rest; nothing deleted).
- `docs/design-plan.md` — design plan: neon palette tokens per theme, Inter + JetBrains Mono (OFL), ASCII layouts, design principles.
- `docs/test-plan.md` — test strategy: core unit, UI smoke (offscreen), performance budgets, CI.
- `STATE.md` rewritten to reflect verified reality only.

### Changed
- Nothing functional in F0; the app is left exactly as found (boot failure at HEAD documented as the starting point).

---

# 📝 Registro de Cambios - KeyMaster Pro

## 🎉 Versión 2.0 - "Master the Digital Realm" (2026-01-05)

### 🆕 Nuevas Características Principales

#### 1. **Modo Constructor de Código Completo**
- ✨ Nuevo modo para escribir código completo con múltiples líneas
- 📝 Editor multilínea que permite usar Enter sin cambiar de ejercicio
- ⌨️ Atajo Ctrl+Enter para verificar código sin necesidad del botón
- 🎯 8 categorías de ejercicios estructurados:
  - Funciones Básicas
  - Práctica de Bucles
  - Operaciones con Listas
  - Operaciones con Diccionarios
  - Clases Básicas
  - Manejo de Errores
  - Operaciones con Archivos
  - Conceptos Avanzados
- 📊 30+ ejercicios de código completo
- ✅ Verificación línea por línea con feedback detallado
- 📈 Aprende la estructura completa de programas Python

#### 2. **Sistema de Notas Educativas "Sabías que..."**
- 💡 Tips contextuales en cada ejercicio
- 📚 17 categorías de tips educativos
- 🎓 Más de 100 notas sobre mejores prácticas, trucos y conceptos
- 🔍 Tips específicos según el concepto que estás practicando
- 💬 Información sobre rendimiento, convenciones y detalles de implementación

#### 3. **Pantalla de Bienvenida con Banner Cyberpunk**
- 🎨 Banner épico "Master the Digital Realm - LUBUNTU EDITION"
- ⚡ Splash screen con animación de carga
- 🖼️ Diseño cyberpunk profesional
- ⏱️ Transición suave a la aplicación principal

#### 4. **Interfaz Adaptativa para Pantallas Pequeñas**
- 📱 Área de juego con scroll automático
- 🔄 Redimensionamiento inteligente de componentes
- 👁️ Mejor visibilidad del botón de verificación
- 📏 Optimización de márgenes y padding

### 🎮 Mejoras en Gamificación

#### Sistema de Logros Expandido
- 🏆 25 logros desbloqueables
- 📊 Categorías: Velocidad, Nivel, Precisión, Supervivencia, Combos, Práctica, Maestría
- 🎯 Notificaciones animadas al desbloquear logros
- 📈 Seguimiento de progreso detallado

#### Power-ups Interactivos
- 💡 Pista: Muestra ayuda contextual
- ⏭️ Saltar: Omite desafío sin penalización
- ⚡ Se ganan al subir de nivel (cada 5 niveles)
- 🎁 Botones visuales con contador de usos

#### Sistema de Combos Mejorado
- 🔥 Indicador visual de combo activo
- 📈 Multiplicador de XP (10% por combo)
- 💥 Efectos de sonido especiales
- 🎯 Combos x5, x10, x25, x50 con logros

### 📚 Contenido de Aprendizaje Expandido

#### Ejercicios Estructurados
- 📝 100+ desafíos de Python organizados
- 🗂️ 11 rutas de aprendizaje
- 🎯 8 categorías de construcción de código
- 📖 Seguimiento de conceptos dominados

#### Rutas de Aprendizaje
1. Fundamentos
2. Estructuras de Datos
3. Control de Flujo
4. Funciones
5. Programación Orientada a Objetos
6. Módulos e Imports
7. Archivos I/O
8. Manejo de Excepciones
9. Conceptos Avanzados
10. Biblioteca Estándar
11. Buenas Prácticas

### 🔧 Mejoras Técnicas

#### Arquitectura Modular
- 📦 Código organizado en 6 módulos especializados:
  - `sound_engine.py`: 7 efectos de sonido procedurales
  - `profile_manager.py`: Sistema completo de progresión
  - `content_generator.py`: Generador de contenido educativo
  - `achievements.py`: Sistema de logros
  - `tips_system.py`: Notas educativas contextuales
  - `splash_screen.py`: Pantalla de bienvenida
- 🎯 Mejor mantenibilidad y extensibilidad
- 📊 Separación clara de responsabilidades

#### Sistema de Audio Mejorado
- 🎵 7 efectos de sonido (antes 4):
  - Click de tecla correcta
  - Error buzz
  - Level up
  - Game over
  - Achievement unlock
  - Combo hit
  - Power-up activation
- 🔊 Generación procedural sin archivos externos

#### Persistencia de Datos Ampliada
- 💾 Perfil más completo:
  - Estadísticas detalladas
  - Conceptos dominados
  - Logros desbloqueados
  - Power-ups disponibles
  - Racha de desafíos diarios
  - Combo más alto
- 📁 Formato JSON legible

### 🎨 Mejoras de UI/UX

#### Interfaz
- 🌈 5 modos de juego con colores distintivos
- 📊 Ventana de estadísticas completa
- 🎯 Indicadores visuales mejorados
- 🔄 Área scrollable para pantallas pequeñas
- 💬 Feedback más detallado

#### Controles
- ⌨️ Ctrl+Enter para verificar código (modo Constructor)
- 🎹 Enter para saltar (otros modos)
- ⚡ Atajos de teclado intuitivos
- 🖱️ Botones de power-up accesibles

#### Visualización
- 📱 Responsivo para diferentes tamaños de pantalla
- 🎨 Colores codificados por estado
- 📊 Barras de progreso dinámicas
- 🏆 Popup de logros animado

### 📈 Estadísticas Rastreadas

- ⚡ WPM más rápido
- 🎯 Precisión de tipeo
- 📝 Total de desafíos completados
- ✨ Desafíos perfectos
- 🏆 Mejor puntuación en Supervivencia
- 🔥 Combo más alto
- 📅 Racha de desafíos diarios
- 🧠 Conceptos de Python dominados
- 🏅 Logros desbloqueados

### 🐛 Correcciones de Bugs

- ✅ Problema de visibilidad del botón en pantallas pequeñas
- ✅ Enter cambiando de ejercicio en modo multilínea (RESUELTO)
- ✅ Optimización de tamaño de componentes
- ✅ Mejor gestión de memoria con scroll

### 📖 Documentación

- 📝 README.md actualizado y expandido
- 📋 Nuevo CHANGELOG.md
- 💡 Instrucciones de uso mejoradas
- 🎯 Ejemplos de cada modo de juego
- 🔧 Guía de instalación actualizada

### 🚀 Rendimiento

- ⚡ Carga más rápida con módulos optimizados
- 💾 Gestión eficiente de memoria
- 🔊 Audio procedural sin archivos
- 📊 Interfaz fluida y responsiva

---

## 📋 Resumen de Archivos Modificados/Creados

### Archivos Nuevos
- ✨ `splash_screen.py` - Pantalla de bienvenida
- ✨ `tips_system.py` - Sistema de notas educativas
- ✨ `test_modules.py` - Script de prueba
- ✨ `CHANGELOG.md` - Este archivo
- ✨ `assets/banner.png` - Banner cyberpunk

### Archivos Actualizados
- 🔧 `keymaster.py` - Integración de nuevas funcionalidades
- 🔧 `content_generator.py` - Ejercicios de código completo
- 🔧 `sound_engine.py` - Nuevos efectos de sonido
- 🔧 `profile_manager.py` - Sistema de progresión ampliado
- 🔧 `achievements.py` - Sistema de logros completo
- 🔧 `README.md` - Documentación actualizada

---

## 🎯 Próximas Mejoras Sugeridas

- [ ] Modo multijugador / competitivo
- [ ] Tablas de clasificación
- [ ] Más categorías de código (Django, FastAPI, etc.)
- [ ] Personalización de temas visuales
- [ ] Estadísticas gráficas de progreso
- [ ] Exportar progreso en PDF
- [ ] Integración con GitHub para snippets reales
- [ ] Modo de práctica con errores comunes

---

**🎉 KeyMaster Pro v2.0 - Una experiencia completa de aprendizaje gamificado para Python!**