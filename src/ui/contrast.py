"""WCAG 2.1 contrast checks for the theme palettes."""

from __future__ import annotations

from dataclasses import dataclass

from src.ui.themes import ThemeColors, ThemeMode, get_theme

AA_NORMAL = 4.5

TEXT_BACKGROUNDS = ("bg_deep", "bg_surface", "bg_panel")
TEXT_ROLES = ("text_primary", "text_secondary", "text_muted")


def _channel(value: float) -> float:
    return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str) -> float:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast_ratio(foreground: str, background: str) -> float:
    lf, lb = relative_luminance(foreground), relative_luminance(background)
    lighter, darker = max(lf, lb), min(lf, lb)
    return (lighter + 0.05) / (darker + 0.05)


@dataclass(frozen=True)
class ContrastResult:
    foreground: str
    background: str
    ratio: float

    @property
    def passes_aa(self) -> bool:
        return self.ratio >= AA_NORMAL


def audit_theme(theme: ThemeColors) -> list[ContrastResult]:
    results = []
    for fg in TEXT_ROLES:
        for bg in TEXT_BACKGROUNDS:
            ratio = contrast_ratio(getattr(theme, fg), getattr(theme, bg))
            results.append(ContrastResult(f"{fg}/{theme.__class__.__name__}", bg, ratio))
    return results


def failing_pairs(mode: ThemeMode, minimum: float = AA_NORMAL) -> list[ContrastResult]:
    theme = get_theme(mode)
    return [r for r in audit_theme(theme) if r.ratio < minimum]


def audit_all_themes() -> dict[str, list[ContrastResult]]:
    return {mode.value: audit_theme(get_theme(mode)) for mode in ThemeMode}
