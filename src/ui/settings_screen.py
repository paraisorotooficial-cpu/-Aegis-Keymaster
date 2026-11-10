"""Settings screen: appearance, sound, typing behaviour, data and profiles."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.core.user_data import UserData
from src.ui import themes
from src.ui.fonts import title_font

THEME_OPTIONS = {"Neon": "neon", "Dark": "dark", "Light": "light"}
EFFECT_OPTIONS = {"Alto": "high", "Medio": "medium", "Bajo": "low", "Off": "off"}
CURSOR_OPTIONS = {"Barra": "bar", "Bloque": "block", "Subrayado": "underline"}
ERROR_MODES = {"Avanzar al fallar": "advance", "Bloquear hasta acertar": "block"}
LANGUAGE_OPTIONS = {"Español": "es", "English": "en"}


class SettingsScreen(QWidget):
    """Renders current settings; emits changes for the app to persist."""

    settings_changed = Signal(str, object)  # key, value
    profile_switched = Signal(str)
    profile_created = Signal(str)

    def __init__(self, user_data: UserData) -> None:
        super().__init__()
        self._user_data = user_data
        self._suspend_signals = False
        self._build()

    def _build(self) -> None:
        column = QVBoxLayout(self)
        column.setContentsMargins(32, 24, 32, 24)
        column.setSpacing(16)

        title = QLabel("Ajustes")
        title.setObjectName("Title")
        title.setFont(title_font())
        column.addWidget(title)

        appearance = self._group()
        form = QFormLayout(appearance)
        self._theme = self._combo(form, "Tema", THEME_OPTIONS, "theme")
        self._effects = self._combo(form, "Nivel de efectos", EFFECT_OPTIONS, "effects_level")
        self._reduce_motion = self._check(form, "Reducir movimiento", "reduce_motion")
        self._font_size = QSpinBox()
        self._font_size.setRange(10, 28)
        self._font_size.setValue(int(self._user_data.settings["font_size"]))
        self._font_size.valueChanged.connect(lambda v: self._change("font_size", v))
        form.addRow("Tamaño de fuente", self._font_size)
        column.addWidget(appearance)

        sound = self._group()
        form = QFormLayout(sound)
        self._sound_enabled = self._check(form, "Sonido activado", "sound_enabled")
        self._volume = QSlider()
        self._volume.setRange(0, 100)
        self._volume.setValue(int(float(self._user_data.settings["volume"]) * 100))
        self._volume.valueChanged.connect(lambda v: self._change("volume", v / 100.0))
        form.addRow("Volumen", self._volume)
        column.addWidget(sound)

        typing = self._group()
        form = QFormLayout(typing)
        self._error_mode = self._combo(form, "Modo de error", ERROR_MODES, "error_mode")
        self._cursor = self._combo(form, "Estilo del cursor", CURSOR_OPTIONS, "cursor_style")
        self._show_keyboard = self._check(form, "Mostrar teclado virtual", "show_keyboard")
        layout_options = {"Autodetectar": "auto", "US": "us", "Latam": "latam", "ES": "es"}
        self._layout_combo = self._combo(form, "Distribución", layout_options, "layout")
        self._ui_language = self._combo(
            form, "Idioma de la interfaz", LANGUAGE_OPTIONS, "ui_language"
        )
        column.addWidget(typing)

        data_row = QHBoxLayout()
        export_csv = QPushButton("Exportar historial a CSV")
        export_csv.clicked.connect(self._export_csv)
        export_json = QPushButton("Exportar historial a JSON")
        export_json.clicked.connect(self._export_json)
        data_row.addWidget(export_csv)
        data_row.addWidget(export_json)
        data_row.addStretch(1)
        column.addLayout(data_row)

        profiles = self._group()
        profile_form = QFormLayout(profiles)
        self._profile_combo = QComboBox()
        self._refresh_profiles()
        self._profile_combo.currentTextChanged.connect(self._on_profile_selected)
        profile_form.addRow("Perfil", self._profile_combo)
        new_profile_row = QHBoxLayout()
        self._new_profile_name = QLabel("Nuevo perfil:")
        new_profile_row.addWidget(self._new_profile_name)
        create = QPushButton("Crear perfil")
        create.clicked.connect(self._on_create_profile)
        new_profile_row.addWidget(create)
        new_profile_row.addStretch(1)
        profile_form.addRow(new_profile_row)
        column.addWidget(profiles)

        column.addStretch(1)

    # -- helpers ---------------------------------------------------

    def _group(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("Panel")
        return frame

    def _combo(self, form: QFormLayout, label: str, options: dict, key: str) -> QComboBox:
        combo = QComboBox()
        for text, value in options.items():
            combo.addItem(text, value)
        current = self._user_data.settings[key]
        index = combo.findData(current)
        combo.setCurrentIndex(max(0, index))
        combo.currentIndexChanged.connect(
            lambda _=0, k=key, c=combo: self._change(k, c.currentData())
        )
        form.addRow(label, combo)
        return combo

    def _check(self, form: QFormLayout, label: str, key: str) -> QCheckBox:
        check = QCheckBox()
        check.setChecked(bool(self._user_data.settings[key]))
        check.toggled.connect(lambda v, k=key: self._change(k, v))
        form.addRow(label, check)
        return check

    def _change(self, key: str, value: object) -> None:
        if self._suspend_signals:
            return
        self._user_data.settings[key] = value
        self.settings_changed.emit(key, value)

    # -- profiles --------------------------------------------------

    def _refresh_profiles(self) -> None:
        from src.core.persistence import ProfileStore

        store = ProfileStore()
        names = store.list_profiles() or [self._user_data.name]
        self._suspend_signals = True
        self._profile_combo.clear()
        self._profile_combo.addItems(names)
        if self._user_data.name in names:
            self._profile_combo.setCurrentText(self._user_data.name)
        self._suspend_signals = False

    def _on_profile_selected(self, name: str) -> None:
        if not self._suspend_signals and name:
            self.profile_switched.emit(name)

    def _on_create_profile(self) -> None:
        from src.core.persistence import ProfileStore

        text, ok = self._ask_text("Nombre del nuevo perfil")
        if not ok or not text.strip():
            return
        store = ProfileStore()
        try:
            store.create_profile(text.strip())
        except FileExistsError:
            QMessageBox.warning(self, "Perfil existente", f"El perfil {text!r} ya existe.")
            return
        self._refresh_profiles()
        self.profile_created.emit(text.strip())

    def _ask_text(self, label: str) -> tuple[str, bool]:
        from PySide6.QtWidgets import QInputDialog

        return QInputDialog.getText(self, "Aegis Keymaster", label)

    # -- export ----------------------------------------------------

    def _export_csv(self) -> None:
        self._export("csv")

    def _export_json(self) -> None:
        self._export("json")

    def _export(self, fmt: str) -> None:
        from pathlib import Path

        from src.core.export import export_history_csv, export_history_json

        path_str, _ = QFileDialog.getSaveFileName(
            self, "Exportar historial", str(Path.home() / f"historial.{fmt}"),
            f"*.{fmt}",
        )
        if not path_str:
            return
        path = Path(path_str)
        if fmt == "json":
            export_history_json(self._user_data.history, path)
        else:
            export_history_csv(self._user_data.history, path)

    # -- sync ------------------------------------------------------

    def reload_from(self, user_data: UserData) -> None:
        """Refresh all controls after a profile switch."""
        self._user_data = user_data
        self._suspend_signals = True
        settings = user_data.settings
        self._theme.setCurrentIndex(self._theme.findData(settings["theme"]))
        self._effects.setCurrentIndex(self._effects.findData(settings["effects_level"]))
        self._reduce_motion.setChecked(bool(settings["reduce_motion"]))
        self._font_size.setValue(int(settings["font_size"]))
        self._sound_enabled.setChecked(bool(settings["sound_enabled"]))
        self._volume.setValue(int(float(settings["volume"]) * 100))
        self._error_mode.setCurrentIndex(self._error_mode.findData(settings["error_mode"]))
        self._cursor.setCurrentIndex(self._cursor.findData(settings["cursor_style"]))
        self._show_keyboard.setChecked(bool(settings["show_keyboard"]))
        self._layout_combo.setCurrentIndex(self._layout_combo.findData(settings["layout"]))
        self._ui_language.setCurrentIndex(self._ui_language.findData(settings["ui_language"]))
        self._refresh_profiles()
        self._suspend_signals = False

    def apply_theme(self, mode: themes.ThemeMode) -> None:
        del mode  # theme is applied app-wide via the stylesheet
