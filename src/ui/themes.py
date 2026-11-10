"""
Theme system for Aegis Keymaster.
Supports Light, Dark and Neon (Cyberpunk) modes with glow/pulse ready colors.
"""

from dataclasses import dataclass
from enum import Enum


class ThemeMode(Enum):
    LIGHT = "light"
    DARK = "dark"
    NEON = "neon"


@dataclass(frozen=True)
class ThemeColors:
    # Backgrounds
    bg_deep: str
    bg_surface: str
    bg_panel: str
    bg_elevated: str

    # Borders & lines
    border: str
    border_strong: str

    # Accents (neon palette)
    cyan: str
    cyan_glow: str
    magenta: str
    magenta_glow: str
    purple: str
    amber: str
    lime: str
    red: str

    # Text
    text_primary: str
    text_secondary: str
    text_muted: str
    text_inverse: str

    # Special
    success: str
    warning: str
    error: str
    key_active: str
    key_error: str
    key_correct: str


# Theme definitions

LIGHT = ThemeColors(
    bg_deep="#F4F6F9",
    bg_surface="#FFFFFF",
    bg_panel="#EEF1F6",
    bg_elevated="#FFFFFF",
    border="#D0D7E2",
    border_strong="#A8B3C5",
    cyan="#0099BB",
    cyan_glow="#00C4E8",
    magenta="#C2185B",
    magenta_glow="#E91E8C",
    purple="#7B1FA2",
    amber="#E65100",
    lime="#2E7D32",
    red="#C62828",
    text_primary="#1A2332",
    text_secondary="#4A5568",
    text_muted="#5D6B80",
    text_inverse="#FFFFFF",
    success="#2E7D32",
    warning="#E65100",
    error="#C62828",
    key_active="#00A8C8",
    key_error="#E53935",
    key_correct="#43A047",
)

DARK = ThemeColors(
    bg_deep="#0A0E14",
    bg_surface="#111820",
    bg_panel="#161E28",
    bg_elevated="#1C2633",
    border="#2A3648",
    border_strong="#3D4F66",
    cyan="#00E5FF",
    cyan_glow="#00F0FF",
    magenta="#FF2BD6",
    magenta_glow="#FF5CE1",
    purple="#A855F7",
    amber="#FFB020",
    lime="#39FF14",
    red="#FF3355",
    text_primary="#E8F1FF",
    text_secondary="#A0B0C8",
    text_muted="#7E8FA9",
    text_inverse="#0A0E14",
    success="#39FF14",
    warning="#FFB020",
    error="#FF3355",
    key_active="#00E5FF",
    key_error="#FF3355",
    key_correct="#39FF14",
)

NEON = ThemeColors(
    bg_deep="#05070B",
    bg_surface="#0B1018",
    bg_panel="#0E1522",
    bg_elevated="#131C2B",
    border="#1E2A3A",
    border_strong="#2A3F55",
    cyan="#00F0FF",
    cyan_glow="#67F6FF",
    magenta="#FF00AA",
    magenta_glow="#FF5CD6",
    purple="#BF5AF2",
    amber="#FFB020",
    lime="#39FF14",
    red="#FF2A55",
    text_primary="#F0F7FF",
    text_secondary="#A8C0D8",
    text_muted="#7C90B0",
    text_inverse="#05070B",
    success="#39FF14",
    warning="#FFB020",
    error="#FF2A55",
    key_active="#00F0FF",
    key_error="#FF2A55",
    key_correct="#39FF14",
)


THEMES: dict[ThemeMode, ThemeColors] = {
    ThemeMode.LIGHT: LIGHT,
    ThemeMode.DARK: DARK,
    ThemeMode.NEON: NEON,
}


def get_theme(mode: ThemeMode | str) -> ThemeColors:
    if isinstance(mode, str):
        mode = ThemeMode(mode.lower())
    return THEMES[mode]


def build_stylesheet(theme: ThemeColors, mode: ThemeMode) -> str:
    """Generate a complete QSS stylesheet for the given theme."""
    del mode  # kept in the signature: future themes may branch on it

    return f"""
    /* Global */
    QMainWindow, QWidget {{
        background-color: {theme.bg_deep};
        color: {theme.text_primary};
        font-family: "Segoe UI", "Ubuntu", "Noto Sans", sans-serif;
        font-size: 14px;
    }}

    QFrame#Card, QFrame#Panel {{
        background-color: {theme.bg_panel};
        border: 1px solid {theme.border};
        border-radius: 12px;
    }}

    QFrame#Elevated {{
        background-color: {theme.bg_elevated};
        border: 1px solid {theme.border};
        border-radius: 10px;
    }}

    QLabel {{
        color: {theme.text_primary};
        background: transparent;
    }}
    QLabel#Muted {{
        color: {theme.text_muted};
    }}
    QLabel#Secondary {{
        color: {theme.text_secondary};
    }}
    QLabel#AccentCyan {{
        color: {theme.cyan};
        font-weight: 600;
    }}
    QLabel#AccentMagenta {{
        color: {theme.magenta};
        font-weight: 600;
    }}
    QLabel#Title {{
        font-size: 22px;
        font-weight: 700;
        color: {theme.text_primary};
        letter-spacing: 0.5px;
    }}
    QLabel#Subtitle {{
        font-size: 13px;
        color: {theme.text_muted};
    }}

    QPushButton {{
        background-color: {theme.bg_elevated};
        color: {theme.text_primary};
        border: 1px solid {theme.border};
        border-radius: 8px;
        padding: 8px 18px;
        font-weight: 600;
        min-height: 18px;
    }}
    QPushButton:hover {{
        background-color: {theme.bg_panel};
        border-color: {theme.cyan};
        color: {theme.cyan};
    }}
    QPushButton:pressed {{
        background-color: {theme.bg_surface};
    }}
    QPushButton:focus, QComboBox:focus, QCheckBox:focus, QListWidget:focus {{
        border: 2px solid {theme.cyan};
        outline: none;
    }}
    QPushButton#Primary {{
        background-color: {theme.cyan};
        color: {theme.text_inverse};
        border: none;
    }}
    QPushButton#Primary:hover {{
        background-color: {theme.cyan_glow};
    }}
    QPushButton#Danger {{
        background-color: transparent;
        color: {theme.red};
        border: 1px solid {theme.red};
    }}
    QPushButton#Danger:hover {{
        background-color: {theme.red};
        color: {theme.text_inverse};
    }}
    QPushButton#Ghost {{
        background: transparent;
        border: 1px solid transparent;
        color: {theme.text_secondary};
    }}
    QPushButton#Ghost:hover {{
        color: {theme.cyan};
        border-color: {theme.border};
    }}

    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {theme.bg_surface};
        color: {theme.text_primary};
        border: 1px solid {theme.border};
        border-radius: 8px;
        padding: 8px 12px;
        selection-background-color: {theme.cyan};
        selection-color: {theme.text_inverse};
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border-color: {theme.cyan};
    }}

    QProgressBar {{
        background-color: {theme.bg_surface};
        border: 1px solid {theme.border};
        border-radius: 6px;
        text-align: center;
        color: {theme.text_primary};
        height: 12px;
    }}
    QProgressBar::chunk {{
        background-color: {theme.cyan};
        border-radius: 5px;
    }}

    QScrollBar:vertical {{
        background: {theme.bg_surface};
        width: 10px;
        margin: 0;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical {{
        background: {theme.border_strong};
        border-radius: 5px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {theme.cyan};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    QTabWidget::pane {{
        border: 1px solid {theme.border};
        border-radius: 10px;
        background: {theme.bg_panel};
        top: -1px;
    }}
    QTabBar::tab {{
        background: {theme.bg_surface};
        color: {theme.text_secondary};
        padding: 8px 20px;
        margin-right: 4px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        border: 1px solid {theme.border};
    }}
    QTabBar::tab:selected {{
        background: {theme.bg_panel};
        color: {theme.cyan};
        border-bottom-color: {theme.bg_panel};
    }}
    QTabBar::tab:hover:!selected {{
        color: {theme.text_primary};
    }}

    QLabel#NeonCyan {{
        color: {theme.cyan};
        font-weight: 700;
    }}
    QLabel#NeonMagenta {{
        color: {theme.magenta};
        font-weight: 700;
    }}
    """
