"""First-run onboarding: at most 3 screens, always skippable."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.core.test_texts import TestTextBank
from src.core.typing_test import TypingTestSession
from src.ui.fonts import subtitle_font, title_font
from src.ui.layouts_combo import fill_layout_combo
from src.ui.typing_area import TypingArea

UI_LANGUAGES = {"es": "Español", "en": "English"}


class WelcomeScreen(QWidget):
    continue_requested = Signal(str, str)  # ui_language, layout
    cancel_requested = Signal()

    def __init__(self, detected_layout: str, ui_language: str = "es") -> None:
        super().__init__()
        column = QVBoxLayout(self)
        column.setSpacing(12)

        title = QLabel("Bienvenido a Aegis Keymaster")
        title.setObjectName("Title")
        title.setFont(title_font())
        subtitle = QLabel(
            "Aprende mecanografía táctil paso a paso. "
            "Puedes omitir esto y cambiarlo después en Ajustes."
        )
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)
        column.addWidget(title)
        column.addWidget(subtitle)

        lang_row = QHBoxLayout()
        lang_label = QLabel("Idioma de la interfaz")
        self.language = QComboBox()
        for code, name in UI_LANGUAGES.items():
            self.language.addItem(name, code)
        self.language.setCurrentIndex(max(0, list(UI_LANGUAGES).index(ui_language)))
        lang_row.addWidget(lang_label)
        lang_row.addWidget(self.language)
        lang_row.addStretch(1)
        column.addLayout(lang_row)

        layout_row = QHBoxLayout()
        layout_label = QLabel("Distribución del teclado")
        self.layout_combo = QComboBox()
        fill_layout_combo(self.layout_combo, detected_layout)
        layout_row.addWidget(layout_label)
        layout_row.addWidget(self.layout_combo)
        layout_row.addStretch(1)
        column.addLayout(layout_row)

        buttons = QHBoxLayout()
        skip = QPushButton("Omitir")
        skip.clicked.connect(self.cancel_requested.emit)
        cont = QPushButton("Continuar")
        cont.clicked.connect(
            lambda: self.continue_requested.emit(
                str(self.language.currentData()), str(self.layout_combo.currentData())
            )
        )
        buttons.addStretch(1)
        buttons.addWidget(skip)
        buttons.addWidget(cont)
        column.addLayout(buttons)
        column.addStretch(1)


class LevelTestScreen(QWidget):
    """One-minute placement test; the result suggests a course starting point."""

    done = Signal(object, object)  # TestResult | None, session | None

    def __init__(self, text_bank: TestTextBank | None = None) -> None:
        super().__init__()
        self._text_bank = text_bank or TestTextBank()
        self._session: TypingTestSession | None = None
        column = QVBoxLayout(self)
        column.setSpacing(12)

        title = QLabel("Test de nivel (1 minuto)")
        title.setObjectName("Title")
        title.setFont(title_font())
        hint = QLabel("Escribe el texto que veas. El cronómetro arranca con la primera pulsación.")
        hint.setObjectName("Muted")
        column.addWidget(title)
        column.addWidget(hint)

        self._typing_area = TypingArea()
        self._typing_area.keyPressed.connect(self._on_char)
        self._typing_area.backspacePressed.connect(self._on_backspace)
        column.addWidget(self._typing_area, 1)

        bottom = QHBoxLayout()
        self._timer_label = QLabel("01:00")
        self._timer_label.setObjectName("Title")
        self._timer_label.setFont(title_font())
        skip = QPushButton("Omitir test")
        skip.clicked.connect(lambda: self.done.emit(None, None))
        bottom.addWidget(self._timer_label)
        bottom.addStretch(1)
        bottom.addWidget(skip)
        column.addLayout(bottom)

    def start(self, language: str = "es") -> None:
        text = self._text_bank.pick(language, 60)
        self._session = TypingTestSession(text, 60)
        self._typing_area.load(text, self._session.states)
        self._typing_area.setFocus()

    def _on_char(self, char: str) -> None:
        if self._session is None:
            return
        self._session.type_char(char)
        self._typing_area.update_state(self._session.position, self._session.states)
        self._timer_label.setText(self._format(self._session.remaining))
        if self._session.finished:
            self._emit_done()

    def _on_backspace(self) -> None:
        if self._session is not None:
            self._session.backspace()
            self._typing_area.update_state(self._session.position, self._session.states)

    def _emit_done(self) -> None:
        self.done.emit(self._session.result() if self._session else None, self._session)

    @staticmethod
    def _format(seconds: float) -> str:
        seconds = max(0, round(seconds))
        return f"{seconds // 60:02d}:{seconds % 60:02d}"


class PlacementResultScreen(QWidget):
    accept_requested = Signal(str)  # recommended lesson id

    def __init__(self) -> None:
        super().__init__()
        column = QVBoxLayout(self)
        column.setSpacing(12)
        title = QLabel("Tu punto de partida")
        title.setObjectName("Title")
        title.setFont(title_font())
        column.addWidget(title)
        self._summary = QLabel()
        self._summary.setWordWrap(True)
        column.addWidget(self._summary)
        self._recommendation = QLabel()
        self._recommendation.setObjectName("Subtitle")
        self._recommendation.setFont(subtitle_font())
        column.addWidget(self._recommendation)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        accept = QPushButton("Empezar curso")
        accept.clicked.connect(lambda: self.accept_requested.emit(self._lesson_id))
        buttons.addWidget(accept)
        column.addLayout(buttons)
        column.addStretch(1)
        self._lesson_id = "L01"

    def show_result(self, result: object) -> None:
        net_wpm = getattr(result, "net_wpm", 0.0) if result is not None else 0.0
        valid = bool(getattr(result, "valid", False))
        if not valid or result is None:
            self._summary.setText(
                "No hay datos suficientes para medir tu nivel; empezamos desde el principio."
            )
            self._lesson_id = "L01"
        elif net_wpm < 20:
            self._summary.setText(
                f"{net_wpm:.0f} WPM netos. Un buen punto de partida es la fila base."
            )
            self._lesson_id = "L01"
        elif net_wpm < 30:
            self._summary.setText(f"{net_wpm:.0f} WPM netos. Puedes empezar por la fila inferior.")
            self._lesson_id = "L06"
        else:
            self._summary.setText(
                f"{net_wpm:.0f} WPM netos. Te recomendamos practicar números y símbolos."
            )
            self._lesson_id = "L09"
        self._recommendation.setText(f"Lección recomendada: {self._lesson_id}")


class OnboardingDialog(QDialog):
    """Three skippable steps: preferences, placement test, recommendation."""

    completed = Signal(dict)  # {"ui_language", "layout", "onboarded", "recommended_lesson"}

    def __init__(
        self, detected_layout: str, ui_language: str = "es", parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Aegis Keymaster — primeros pasos")
        self.setMinimumSize(720, 480)
        self._result: dict = {"ui_language": ui_language, "layout": detected_layout}

        self.stack = QStackedWidget()
        self.welcome = WelcomeScreen(detected_layout, ui_language)
        self.level_test = LevelTestScreen()
        self.placement = PlacementResultScreen()
        self.stack.addWidget(self.welcome)
        self.stack.addWidget(self.level_test)
        self.stack.addWidget(self.placement)

        column = QVBoxLayout(self)
        column.addWidget(self.stack)

        self.welcome.continue_requested.connect(self._on_welcome_continue)
        self.welcome.cancel_requested.connect(self._finish)
        self.level_test.done.connect(self._on_level_done)
        self.placement.accept_requested.connect(lambda lesson: self._finish(lesson))

        self.stack.setCurrentWidget(self.welcome)

    def _on_welcome_continue(self, ui_language: str, layout: str) -> None:
        self._result["ui_language"] = ui_language
        self._result["layout"] = layout
        self.level_test.start("es")
        self.stack.setCurrentWidget(self.level_test)

    def _on_level_done(self, result: object, session: object) -> None:
        if result is not None:
            self._result["placement_result"] = result  # type: ignore[assignment]
        self.placement.show_result(result)
        self.stack.setCurrentWidget(self.placement)

    def _finish(self, recommended_lesson: str = "L01") -> None:
        self._result["onboarded"] = True
        self._result["recommended_lesson"] = recommended_lesson
        self.completed.emit(self._result)
        self.accept()
