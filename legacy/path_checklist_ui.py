"""Path checklist UI for KeyMaster — Phase 2.2."""
import customtkinter as ctk

THEME = {
    "bg": "#05070B", "surface": "#0B1018", "surface2": "#111827", "panel": "#0E1522",
    "border": "#1E2A3A", "cyan": "#00E5FF", "cyan_dim": "#00A8B8", "magenta": "#FF2BD6",
    "amber": "#FFB020", "lime": "#39FF14", "text": "#E8F1FF", "muted": "#6B7C93", "ghost": "#3A4A5C",
}


class PathChecklistMixin:
    def _build_path_checklist_widgets(self, path_frame):
        self.lbl_path_progress = ctk.CTkLabel(
            path_frame, text="Progreso 0/0",
            font=("Segoe UI", 11), text_color=THEME["muted"],
        )
        self.lbl_path_progress.pack(pady=(0, 2))
        self.path_progress_bar = ctk.CTkProgressBar(
            path_frame, width=220, height=8,
            progress_color=THEME["cyan"], fg_color=THEME["surface2"], corner_radius=4,
        )
        self.path_progress_bar.pack(pady=(0, 4))
        self.path_progress_bar.set(0)
        self.path_check_frame = ctk.CTkFrame(path_frame, fg_color="transparent")
        self.path_check_frame.pack(fill="x", padx=8, pady=(0, 6))
        self.btn_path_checklist = ctk.CTkButton(
            path_frame, text="Checklist de ruta", width=160, height=26,
            font=("Segoe UI", 11, "bold"),
            fg_color=THEME["surface2"], hover_color=THEME["cyan_dim"],
            border_width=1, border_color=THEME["cyan"], text_color=THEME["text"],
            command=self._show_path_checklist,
        )
        self.btn_path_checklist.pack(pady=(0, 8))

    def _refresh_path_checklist(self):
        if not hasattr(self, "lbl_path_progress"):
            return
        path = getattr(self, "current_learning_path", "basics")
        try:
            rows = self.content.get_path_checklist(
                path,
                concept_stats=getattr(self.player, "concept_stats", {}) or {},
                completed_concepts=getattr(self.player, "completed_concepts", set()) or set(),
            )
        except Exception:
            rows = []
        total = max(1, len(rows))
        done = sum(1 for r in rows if r.get("status") == "mastered")
        learning = sum(1 for r in rows if r.get("status") == "learning")
        due = sum(1 for r in rows if r.get("status") == "due")
        try:
            name = self.content.get_path_name(path)
        except Exception:
            name = path
        extra = ""
        if learning:
            extra += f" · {learning} en curso"
        if due:
            extra += f" · {due} due"
        self.lbl_path_progress.configure(text=f"{name}: {done}/{len(rows)} dominados{extra}")
        try:
            self.path_progress_bar.set(min(1.0, done / total))
        except Exception:
            pass
        if hasattr(self, "path_check_frame"):
            for w in self.path_check_frame.winfo_children():
                w.destroy()
            marks = {"mastered": "✓", "learning": "…", "due": "!", "todo": "○"}
            colors = {
                "mastered": THEME["lime"],
                "learning": THEME["cyan"],
                "due": THEME["amber"],
                "todo": THEME["ghost"],
            }
            for r in rows[:10]:
                st = r.get("status", "todo")
                ctk.CTkLabel(
                    self.path_check_frame,
                    text=f"{marks.get(st, '○')} {r.get('concept', '?')}",
                    font=("Segoe UI", 10),
                    text_color=colors.get(st, THEME["muted"]),
                ).pack(anchor="w", padx=4, pady=0)

    def _show_path_checklist(self):
        path = getattr(self, "current_learning_path", "basics")
        try:
            rows = self.content.get_path_checklist(
                path,
                concept_stats=getattr(self.player, "concept_stats", {}) or {},
                completed_concepts=getattr(self.player, "completed_concepts", set()) or set(),
            )
        except Exception:
            rows = []
        try:
            name = self.content.get_path_name(path)
        except Exception:
            name = path

        win = ctk.CTkToplevel(self)
        win.title(f"KeyMaster // RUTA · {name}")
        win.geometry("420x480")
        win.configure(fg_color=THEME["bg"])
        try:
            win.transient(self)
        except Exception:
            pass
        ctk.CTkLabel(
            win, text=f"◈ CHECKLIST · {name}",
            font=("Segoe UI", 16, "bold"), text_color=THEME["cyan"],
        ).pack(pady=(14, 4))
        done = sum(1 for r in rows if r.get("status") == "mastered")
        ctk.CTkLabel(
            win, text=f"{done}/{len(rows)} conceptos dominados",
            font=("Segoe UI", 12), text_color=THEME["muted"],
        ).pack(pady=(0, 8))
        bar = ctk.CTkProgressBar(win, width=300, height=10, progress_color=THEME["cyan"], fg_color=THEME["surface2"])
        bar.pack(pady=(0, 10))
        bar.set(min(1.0, done / max(1, len(rows))))

        scroll = ctk.CTkScrollableFrame(win, fg_color=THEME["surface"], corner_radius=10)
        scroll.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        labels = {
            "mastered": ("✓ Dominado", THEME["lime"]),
            "learning": ("… En curso", THEME["cyan"]),
            "due": ("! Revisar (FSRS)", THEME["amber"]),
            "todo": ("○ Pendiente", THEME["ghost"]),
        }
        for r in rows:
            st = r.get("status", "todo")
            lab, color = labels.get(st, ("○", THEME["muted"]))
            card = ctk.CTkFrame(scroll, fg_color=THEME["panel"], corner_radius=8, border_width=1, border_color=color)
            card.pack(fill="x", padx=6, pady=4)
            ctk.CTkLabel(
                card, text=f"{lab}  ·  {r.get('concept', '?')}",
                font=("Segoe UI", 13, "bold"), text_color=color, anchor="w",
            ).pack(anchor="w", padx=10, pady=(8, 2))
            ctk.CTkLabel(
                card,
                text=f"intentos {r.get('attempts', 0)}  ·  ok {r.get('successes', 0)}  ·  fallos {r.get('fails', 0)}",
                font=("Segoe UI", 11), text_color=THEME["muted"], anchor="w",
            ).pack(anchor="w", padx=10, pady=(0, 8))

        ctk.CTkButton(
            win, text="Cerrar", width=100, height=30, command=win.destroy,
            fg_color=THEME["surface2"], hover_color=THEME["panel"],
            border_width=1, border_color=THEME["border"], text_color=THEME["text"],
        ).pack(pady=(0, 14))
