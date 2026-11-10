"""FSRS due-review banner for KeyMaster — Phase 1.4."""
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


class FsrsBannerMixin:
    """Startup / in-session banner for spaced-repetition due items."""

    def _build_fsrs_banner(self, parent):
        self._fsrs_dismissed = False
        self.fsrs_banner = ctk.CTkFrame(
            parent,
            fg_color=THEME["panel"],
            corner_radius=10,
            border_width=1,
            border_color=THEME["amber"],
        )
        inner = ctk.CTkFrame(self.fsrs_banner, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=8)

        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)
        self.lbl_fsrs_title = ctk.CTkLabel(
            left,
            text="◈ FSRS · sin revisiones pendientes",
            font=("Segoe UI", 13, "bold"),
            text_color=THEME["amber"],
            anchor="w",
        )
        self.lbl_fsrs_title.pack(anchor="w")
        self.lbl_fsrs_detail = ctk.CTkLabel(
            left,
            text="",
            font=("Segoe UI", 11),
            text_color=THEME["muted"],
            anchor="w",
            justify="left",
        )
        self.lbl_fsrs_detail.pack(anchor="w")

        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="right")
        self.btn_fsrs_review = ctk.CTkButton(
            right,
            text="Repasar ahora",
            width=120,
            height=28,
            font=("Segoe UI", 12, "bold"),
            fg_color=THEME["amber"],
            hover_color="#E09A10",
            text_color=THEME["bg"],
            command=self._on_fsrs_review,
        )
        self.btn_fsrs_review.pack(side="left", padx=4)
        self.btn_fsrs_later = ctk.CTkButton(
            right,
            text="Mas tarde",
            width=90,
            height=28,
            font=("Segoe UI", 11),
            fg_color=THEME["surface2"],
            hover_color=THEME["panel"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["text"],
            command=self._on_fsrs_dismiss,
        )
        self.btn_fsrs_later.pack(side="left", padx=4)
        self._fsrs_banner_visible = False

    def _refresh_fsrs_banner(self, force: bool = False):
        if getattr(self, "_fsrs_dismissed", False) and not force:
            return
        if not hasattr(self, "fsrs_banner"):
            return
        try:
            due = list(self.player.get_due_concepts(limit=8) or [])
        except Exception:
            due = []

        if not due:
            if self._fsrs_banner_visible:
                try:
                    self.fsrs_banner.pack_forget()
                except Exception:
                    pass
                self._fsrs_banner_visible = False
            return

        n = len(due)
        sample = ", ".join(due[:4])
        extra = f"  (+{n - 4})" if n > 4 else ""
        title = f"◈ FSRS · {n} revision{'es' if n != 1 else ''} pendiente{'s' if n != 1 else ''}"
        detail = f"{sample}{extra}"
        try:
            self.lbl_fsrs_title.configure(text=title, text_color=THEME["amber"])
            self.lbl_fsrs_detail.configure(text=detail)
        except Exception:
            pass

        if not self._fsrs_banner_visible:
            try:
                self.fsrs_banner.pack(fill="x", pady=(4, 8), before=getattr(self, "lbl_diff", None) or None)
            except Exception:
                try:
                    self.fsrs_banner.pack(fill="x", pady=(4, 8))
                except Exception:
                    pass
            self._fsrs_banner_visible = True

    def _on_fsrs_dismiss(self):
        self._fsrs_dismissed = True
        if hasattr(self, "fsrs_banner"):
            try:
                self.fsrs_banner.pack_forget()
            except Exception:
                pass
        self._fsrs_banner_visible = False
        try:
            self.lbl_feedback.configure(
                text="// Revisiones FSRS pospuestas · reaparecen al reiniciar",
                text_color=THEME["ghost"],
            )
        except Exception:
            pass

    def _on_fsrs_review(self):
        self._fsrs_dismissed = False
        try:
            due = list(self.player.get_due_concepts(limit=8) or [])
        except Exception:
            due = []
        try:
            self.mode_panel.set("APRENDIZAJE")
        except Exception:
            pass
        self._set_mode("LEARNING")
        try:
            self._sync_learner_context()
        except Exception:
            pass
        if due:
            try:
                self.lbl_feedback.configure(
                    text=f"◈ Repaso FSRS · foco: {', '.join(due[:3])}",
                    text_color=THEME["amber"],
                )
            except Exception:
                pass
        self._refresh_fsrs_banner(force=True)

    def _maybe_show_fsrs_banner(self):
        if getattr(self, "_fsrs_dismissed", False):
            return
        try:
            from onboarding import needs_onboarding
            if needs_onboarding(self.player):
                return
        except Exception:
            if not bool(getattr(self.player, "onboarding_done", True)):
                return
        self._refresh_fsrs_banner(force=True)
