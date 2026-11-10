"""Simple i18n: inline string tables, es default, en available."""

from __future__ import annotations

STRINGS: dict[str, dict[str, str]] = {
    "es": {
        "nav.course": "Curso",
        "nav.test": "Test",
        "nav.progress": "Progreso",
        "nav.settings": "Ajustes",
        "course.title": "Curso de mecanografía",
        "course.subtitle": "Supera una lección para desbloquear la siguiente.",
        "course.review": "Repasar teclas débiles",
        "course.start": "Empezar",
        "lesson.back": "← Volver",
        "lesson.retry": "Reintentar",
        "lesson.continue": "Continuar",
        "test.title": "Test cronometrado",
        "test.subtitle": "Elige la duración y mide tu velocidad real.",
        "test.start": "Empezar test",
        "test.abort": "Abandonar",
        "test.repeat": "Repetir test",
        "test.review": "Repasar teclas débiles",
        "test.hint": "Empieza a escribir para arrancar el cronómetro.",
        "test.language": "Idioma del texto:",
        "settings.title": "Ajustes",
        "settings.save": "Guardar ajustes",
    },
    "en": {
        "nav.course": "Course",
        "nav.test": "Test",
        "nav.progress": "Progress",
        "nav.settings": "Settings",
        "course.title": "Typing course",
        "course.subtitle": "Pass a lesson to unlock the next one.",
        "course.review": "Review weak keys",
        "course.start": "Start",
        "lesson.back": "← Back",
        "lesson.retry": "Retry",
        "lesson.continue": "Continue",
        "test.title": "Timed test",
        "test.subtitle": "Choose a duration and measure your real speed.",
        "test.start": "Start test",
        "test.abort": "Quit",
        "test.repeat": "Repeat test",
        "test.review": "Review weak keys",
        "test.hint": "Start typing to begin the countdown.",
        "test.language": "Text language:",
        "settings.title": "Settings",
        "settings.save": "Save settings",
    },
}

_language = "es"


def set_language(code: str) -> None:
    global _language
    if code in STRINGS:
        _language = code


def current_language() -> str:
    return _language


def tr(key: str) -> str:
    table = STRINGS.get(_language, STRINGS["es"])
    return table.get(key) or STRINGS["es"].get(key) or key
