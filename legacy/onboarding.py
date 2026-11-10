"""First-run onboarding (~60s) for KeyMaster — Phase 1.3."""
from __future__ import annotations
import customtkinter as ctk

THEME = {
    "bg": "#05070B",
    "surface": "#0B1018",
    "surface2": "#111827",
    "panel": "#0E1522",
    "border": "#1E2A3A",
    "cyan": "#00E5FF",
    "cyan_dim": "#00A8B8",
    "magenta": "#FF2BD6",
    "amber": "#FFB020",
    "lime": "#39FF14",
    "text": "#E8F1FF",
    "muted": "#6B7C93",
    "ghost": "#3A4A5C",
}

LEVEL_PRESETS = {
    "novato": {
        "label": "Novato",
        "desc": "Empiezo con Python o vuelvo tras un descanso",
        "level": 1,
        "path": "basics",
        "xp": 0,
    },
    "intermedio": {
        "label": "Intermedio",
        "desc": "Se variables, if/for y funciones basicas",
        "level": 5,
        "path": "functions",
        "xp": 50,
    },
    "avanzado": {
        "label": "Avanzado",
        "desc": "Clases, comprensiones y manejo de errores",
        "level": 12,
        "path": "oop",
        "xp": 100,
    },
}

PATH_ALIASES = {
    "basics": ["basics", "basicos", "basic", "fundamentos", "intro"],
    "functions": ["functions", "funciones", "funcs"],
    "oop": ["oop", "classes", "clases", "objects"],
}


def resolve_path(available: list, preferred_key: str) -> str:
    if not available:
        return preferred_key
    aliases = PATH_ALIASES.get(preferred_key, [preferred_key])
    low = {a.lower(): a for a in available}
    for alias in aliases:
        if alias.lower() in low:
            return low[alias.lower()]
    for a in available:
        for alias in aliases:
            if alias.lower() in a.lower():
                return a
    return available[0]


class OnboardingDialog(ctk.CTkToplevel):
    """Modal 3-step onboarding: level → path → mini demo tip."""

    def __init__(self, master, available_paths: list | None = None, on_done=None):
        super().__init__(master)
        self.on_done = on_done
        self.available_paths = available_paths or ["basics"]
        self.result = None
        self.choice_key = "novato"
        self.path_choice = resolve_path(self.available_paths, "basics")

        self.title("KeyMaster // BIENVENIDA")
        self.geometry("520x560")
        self.configure(fg_color=THEME["bg"])
        self.resizable(False, False)
        try:
            self.transient(master)
            self.grab_set()
        except Exception:
            pass

        self.step = 0
        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True, padx=20, pady=16)
        self._footer = ctk.CTkFrame(self, fg_color="transparent")
        self._footer.pack(fill="x", padx=20, pady=(0, 16))
        self._render()

    def _clear_body(self):
        for w in self._body.winfo_children():
            w.destroy()
        for w in self._footer.winfo_children():
            w.destroy()

    def _render(self):
        self._clear_body()
        if self.step == 0:
            self._step_level()
        elif self.step == 1:
            self._step_path()
        else:
            self._step_ready()

    def _step_level(self):
        ctk.CTkLabel(
            self._body, text="◈ BIENVENIDO A KEYMASTER",
            font=("Segoe UI", 18, "bold"), text_color=THEME["cyan"],
        ).pack(pady=(8, 4))
        ctk.CTkLabel(
            self._body,
            text="60 segundos para calibrar tu ruta.\nComo te sientes con Python ahora?",
            font=("Segoe UI", 13), text_color=THEME["muted"], justify="center",
        ).pack(pady=(0, 16))

        self._level_var = ctk.StringVar(value=self.choice_key)
        for key, preset in LEVEL_PRESETS.items():
            card = ctk.CTkFrame(
                self._body, fg_color=THEME["panel"], corner_radius=10,
                border_width=1, border_color=THEME["border"],
            )
            card.pack(fill="x", pady=5)

            def _select(k=key, c=card):
                self.choice_key = k
                self._level_var.set(k)
                for child in self._body.winfo_children():
                    if isinstance(child, ctk.CTkFrame):
                        try:
                            child.configure(border_color=THEME["border"])
                        except Exception:
                            pass
                c.configure(border_color=THEME["cyan"])

            btn = ctk.CTkRadioButton(
                card, text=f"{preset['label']}  —  {preset['desc']}",
                variable=self._level_var, value=key, command=_select,
                font=("Segoe UI", 13), text_color=THEME["text"],
                fg_color=THEME["cyan"], hover_color=THEME["cyan_dim"],
            )
            btn.pack(anchor="w", padx=12, pady=12)
            if key == self.choice_key:
                card.configure(border_color=THEME["cyan"])

        ctk.CTkButton(
            self._footer, text="Siguiente →", height=36, width=140,
            font=("Segoe UI", 13, "bold"),
            fg_color=THEME["cyan"], hover_color=THEME["cyan_dim"], text_color=THEME["bg"],
            command=self._next,
        ).pack(side="right")

    def _step_path(self):
        preset = LEVEL_PRESETS[self.choice_key]
        suggested = resolve_path(self.available_paths, preset["path"])
        self.path_choice = suggested

        ctk.CTkLabel(
            self._body, text="◈ RUTA INICIAL",
            font=("Segoe UI", 18, "bold"), text_color=THEME["magenta"],
        ).pack(pady=(8, 4))
        ctk.CTkLabel(
            self._body,
            text=f"Sugerida para nivel {preset['label']}: {suggested}\nPuedes cambiarla cuando quieras.",
            font=("Segoe UI", 13), text_color=THEME["muted"], justify="center",
        ).pack(pady=(0, 12))

        self._path_var = ctk.StringVar(value=suggested)
        menu = ctk.CTkOptionMenu(
            self._body, values=self.available_paths, variable=self._path_var,
            width=280, font=("Segoe UI", 13),
            fg_color=THEME["surface2"], button_color=THEME["magenta"],
            button_hover_color=THEME["cyan"], text_color=THEME["text"],
            dropdown_fg_color=THEME["panel"], dropdown_hover_color=THEME["surface2"],
            dropdown_text_color=THEME["text"],
        )
        menu.pack(pady=8)

        tip = ctk.CTkFrame(self._body, fg_color=THEME["panel"], corner_radius=10, border_width=1, border_color=THEME["amber"])
        tip.pack(fill="x", pady=16)
        ctk.CTkLabel(
            tip, text="Demo rapida",
            font=("Segoe UI", 12, "bold"), text_color=THEME["amber"],
        ).pack(anchor="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(
            tip,
            text="En Aprendizaje veras retos con huecos ____.\nEscribe solo lo que falta y pulsa Enter.\nEn Constructor verificas codigo real con tests.",
            font=("Segoe UI", 12), text_color=THEME["text"], justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 10))

        ctk.CTkButton(
            self._footer, text="← Atras", height=36, width=100,
            fg_color=THEME["surface2"], hover_color=THEME["panel"],
            border_width=1, border_color=THEME["border"], text_color=THEME["text"],
            command=self._back,
        ).pack(side="left")
        ctk.CTkButton(
            self._footer, text="Siguiente →", height=36, width=140,
            font=("Segoe UI", 13, "bold"),
            fg_color=THEME["magenta"], hover_color=THEME["cyan"], text_color=THEME["bg"],
            command=self._next,
        ).pack(side="right")

    def _step_ready(self):
        preset = LEVEL_PRESETS[self.choice_key]
        path = getattr(self, "_path_var", None)
        self.path_choice = path.get() if path else self.path_choice

        ctk.CTkLabel(
            self._body, text="◈ LISTO PARA ORBITA",
            font=("Segoe UI", 18, "bold"), text_color=THEME["lime"],
        ).pack(pady=(8, 4))
        ctk.CTkLabel(
            self._body,
            text=(
                f"Nivel inicial: {preset['label']} (LVL {preset['level']})\n"
                f"Ruta: {self.path_choice}\n\n"
                "Te llevamos a Aprendizaje con un hueco de practica.\n"
                "Completa contratos diarios para bonus XP."
            ),
            font=("Segoe UI", 13), text_color=THEME["text"], justify="center",
        ).pack(pady=12)

        checklist = ctk.CTkFrame(self._body, fg_color=THEME["panel"], corner_radius=10, border_width=1, border_color=THEME["lime"])
        checklist.pack(fill="x", pady=8)
        for line in (
            "Chip CONTRATOS arriba a la derecha",
            "Stats → telemetria y FSRS",
            "Constructor → tests reales",
            "IA local opcional (Ollama)",
        ):
            ctk.CTkLabel(
                checklist, text=f"  ·  {line}",
                font=("Segoe UI", 12), text_color=THEME["muted"], anchor="w",
            ).pack(anchor="w", padx=10, pady=3)

        ctk.CTkButton(
            self._footer, text="← Atras", height=36, width=100,
            fg_color=THEME["surface2"], hover_color=THEME["panel"],
            border_width=1, border_color=THEME["border"], text_color=THEME["text"],
            command=self._back,
        ).pack(side="left")
        ctk.CTkButton(
            self._footer, text="Empezar →", height=36, width=160,
            font=("Segoe UI", 13, "bold"),
            fg_color=THEME["lime"], hover_color="#2BD910", text_color=THEME["bg"],
            command=self._finish,
        ).pack(side="right")

    def _next(self):
        if self.step == 1 and hasattr(self, "_path_var"):
            self.path_choice = self._path_var.get()
        self.step = min(2, self.step + 1)
        self._render()

    def _back(self):
        self.step = max(0, self.step - 1)
        self._render()

    def _finish(self):
        if hasattr(self, "_path_var"):
            self.path_choice = self._path_var.get()
        preset = LEVEL_PRESETS[self.choice_key]
        self.result = {
            "level_key": self.choice_key,
            "level": preset["level"],
            "path": self.path_choice,
            "xp": preset["xp"],
            "label": preset["label"],
        }
        try:
            self.grab_release()
        except Exception:
            pass
        if callable(self.on_done):
            try:
                self.on_done(self.result)
            except Exception:
                pass
        self.destroy()


def needs_onboarding(player) -> bool:
    return not bool(getattr(player, "onboarding_done", False))


def apply_onboarding_result(player, result: dict) -> None:
    if not result:
        return
    player.onboarding_done = True
    player.onboarding_level_key = result.get("level_key", "novato")
    try:
        player.level = max(1, int(result.get("level") or 1))
        player.xp = max(0, int(result.get("xp") or 0))
    except Exception:
        pass
    path = result.get("path") or "basics"
    player.current_learning_path = path
    try:
        player.save_profile()
    except Exception:
        pass
