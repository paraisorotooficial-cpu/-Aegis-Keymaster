# Changelog — Aegis Keymaster

All notable changes to the PySide6 typing tutor are documented here. Entries for the pre-redesign "KeyMaster Pro" CustomTkinter app are kept below.

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