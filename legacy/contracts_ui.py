"""Daily contracts UI helpers for KeyMaster (Phase 1.2)."""
import customtkinter as ctk

THEME = {
    "bg": "#05070B", "surface": "#0B1018", "surface2": "#111827", "panel": "#0E1522",
    "border": "#1E2A3A", "cyan": "#00E5FF", "cyan_dim": "#00A8B8", "magenta": "#FF2BD6",
    "amber": "#FFB020", "lime": "#39FF14", "red": "#FF3355", "text": "#E8F1FF",
    "muted": "#6B7C93", "ghost": "#3A4A5C",
}


class ContractsUIMixin:
    """Header chip + dedicated contracts panel + claim flow."""

    def _build_contracts_chip(self, parent):
        self._contracts_win = None
        self.contracts_chip = ctk.CTkFrame(
            parent, fg_color=THEME["panel"], corner_radius=8,
            border_width=1, border_color=THEME["amber"],
        )
        self.contracts_chip.pack(anchor="e", pady=(0, 4))
        chip_inner = ctk.CTkFrame(self.contracts_chip, fg_color="transparent")
        chip_inner.pack(padx=8, pady=4)
        self.lbl_contracts = ctk.CTkLabel(
            chip_inner, text="◈ CONTRATOS  0/3",
            font=("Segoe UI", 11, "bold"), text_color=THEME["amber"], cursor="hand2",
        )
        self.lbl_contracts.pack(anchor="w")
        self.contracts_bar = ctk.CTkProgressBar(
            chip_inner, width=110, height=6, progress_color=THEME["amber"],
            fg_color=THEME["surface2"], corner_radius=3,
        )
        self.contracts_bar.pack(anchor="w", pady=(2, 0))
        self.contracts_bar.set(0)
        self.lbl_contracts_hint = ctk.CTkLabel(
            chip_inner, text="click → detalle",
            font=("Segoe UI", 9), text_color=THEME["ghost"],
        )
        self.lbl_contracts_hint.pack(anchor="w")
        for w in (self.contracts_chip, chip_inner, self.lbl_contracts, self.contracts_bar, self.lbl_contracts_hint):
            try:
                w.bind("<Button-1>", lambda e: self._show_contracts_panel())
            except Exception:
                pass

    def _refresh_contracts_label(self):
        try:
            info = self.player.get_contracts_progress()
            done, total = info.get("done", 0), info.get("total", 3)
            total = max(1, total)
            frac = min(1.0, done / total)
            if info.get("claimed"):
                txt, color, bar_c = f"◈ CONTRATOS  {done}/{total} ✓", THEME["lime"], THEME["lime"]
                hint = "bonus reclamado"
            elif info.get("all_done"):
                txt, color, bar_c = f"◈ CONTRATOS  {done}/{total} · RECLAMA", THEME["amber"], THEME["amber"]
                hint = "click → reclamar XP"
            else:
                txt, color, bar_c = f"◈ CONTRATOS  {done}/{total}", THEME["amber"], THEME["amber"]
                hint = "click → detalle"
            if hasattr(self, "lbl_contracts"):
                self.lbl_contracts.configure(text=txt, text_color=color)
            if hasattr(self, "contracts_bar"):
                self.contracts_bar.configure(progress_color=bar_c)
                self.contracts_bar.set(frac)
            if hasattr(self, "lbl_contracts_hint"):
                self.lbl_contracts_hint.configure(
                    text=hint,
                    text_color=THEME["ghost"] if not info.get("all_done") else THEME["amber"],
                )
            if hasattr(self, "contracts_chip"):
                border = THEME["lime"] if info.get("claimed") else THEME["amber"]
                self.contracts_chip.configure(border_color=border)
        except Exception:
            pass

    def _toast_contract(self, message: str, color=None):
        color = color or THEME["amber"]
        try:
            self.lbl_feedback.configure(text=message, text_color=color)
        except Exception:
            pass

    def _claim_contracts(self):
        try:
            bonus = self.player.claim_contracts_bonus()
            if bonus:
                self._toast_contract(f"◆ Misiones del dia completadas · +{bonus} XP", THEME["lime"])
                self.lbl_level.configure(text=f"LVL {self.player.level}")
                need = max(1, self.player.xp_for_next_level)
                self.progress.set(min(1.0, self.player.xp / need))
                try:
                    self.audio.play_levelup()
                except Exception:
                    pass
            else:
                info = self.player.get_contracts_progress()
                if not info.get("all_done"):
                    self._toast_contract(
                        f"Contratos {info.get('done', 0)}/{info.get('total', 3)} — sigue practicando",
                        THEME["muted"],
                    )
                else:
                    self._toast_contract("Bonus de contratos ya reclamado hoy", THEME["ghost"])
            self._refresh_contracts_label()
        except Exception as e:
            self._toast_contract(f"Contratos: {e}", THEME["red"])

    def _show_contracts_panel(self):
        if getattr(self, "_contracts_win", None) is not None:
            try:
                if self._contracts_win.winfo_exists():
                    self._contracts_win.lift()
                    self._contracts_win.focus()
                    return
            except Exception:
                pass
        try:
            info = self.player.get_contracts_progress()
        except Exception:
            info = {
                "contracts": [], "done": 0, "total": 3,
                "all_done": False, "claimed": False, "date": "?",
            }

        win = ctk.CTkToplevel(self)
        self._contracts_win = win
        win.title("KeyMaster // CONTRATOS")
        win.geometry("460x420")
        win.configure(fg_color=THEME["bg"])
        try:
            win.transient(self)
        except Exception:
            pass

        ctk.CTkLabel(
            win, text="◈ CONTRATOS DEL DIA",
            font=("Segoe UI", 18, "bold"), text_color=THEME["amber"],
        ).pack(pady=(16, 2))
        ctk.CTkLabel(
            win,
            text=f"Fecha {info.get('date', '?')}  ·  {info.get('done', 0)}/{info.get('total', 3)} completados",
            font=("Segoe UI", 12), text_color=THEME["muted"],
        ).pack(pady=(0, 8))

        bar = ctk.CTkProgressBar(
            win, width=360, height=10, progress_color=THEME["amber"],
            fg_color=THEME["surface2"], corner_radius=4,
        )
        bar.pack(pady=(0, 12))
        total = max(1, int(info.get("total") or 3))
        bar.set(min(1.0, int(info.get("done") or 0) / total))

        body = ctk.CTkScrollableFrame(
            win, fg_color=THEME["surface"], corner_radius=10,
            scrollbar_button_color=THEME["cyan_dim"],
            scrollbar_button_hover_color=THEME["cyan"],
        )
        body.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        contracts = info.get("contracts") or []
        if not contracts:
            ctk.CTkLabel(
                body,
                text="// Sin contratos generados. Reinicia la app.",
                font=("Segoe UI", 13), text_color=THEME["ghost"], justify="center",
            ).pack(pady=30)
        for c in contracts:
            done = bool(c.get("done"))
            card = ctk.CTkFrame(
                body, fg_color=THEME["panel"], corner_radius=10,
                border_width=1, border_color=THEME["lime"] if done else THEME["border"],
            )
            card.pack(fill="x", padx=6, pady=5)
            head = ctk.CTkFrame(card, fg_color="transparent")
            head.pack(fill="x", padx=10, pady=(8, 2))
            mark = "✓" if done else "○"
            ctk.CTkLabel(
                head, text=f"{mark}  {c.get('label', c.get('id', '?'))}",
                font=("Segoe UI", 13, "bold"),
                text_color=THEME["lime"] if done else THEME["text"],
                anchor="w", justify="left", wraplength=380,
            ).pack(side="left", fill="x", expand=True)
            prog = int(c.get("progress") or 0)
            tgt = max(1, int(c.get("target") or 1))
            ctk.CTkLabel(
                head, text=f"{prog}/{tgt}",
                font=("Segoe UI", 12, "bold"),
                text_color=THEME["lime"] if done else THEME["cyan"],
            ).pack(side="right")
            pbar = ctk.CTkProgressBar(
                card, height=6,
                progress_color=THEME["lime"] if done else THEME["cyan"],
                fg_color=THEME["surface2"], corner_radius=3,
            )
            pbar.pack(fill="x", padx=10, pady=(0, 4))
            pbar.set(min(1.0, prog / tgt))
            xp = c.get("xp", 20)
            ctk.CTkLabel(
                card, text=f"Recompensa parcial: +{xp} XP al cerrar el dia",
                font=("Segoe UI", 10), text_color=THEME["muted"],
            ).pack(anchor="w", padx=10, pady=(0, 8))

        footer = ctk.CTkFrame(win, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=(4, 16))
        if info.get("all_done") and not info.get("claimed"):
            bonus = sum(int(c.get("xp") or 0) for c in contracts) + 15
            ctk.CTkButton(
                footer, text=f"Reclamar bonus  +{bonus} XP",
                height=36, font=("Segoe UI", 13, "bold"),
                fg_color=THEME["amber"], hover_color="#E09A10", text_color=THEME["bg"],
                command=lambda: (self._claim_contracts(), win.destroy()),
            ).pack(side="left", padx=(0, 8))
        elif info.get("claimed"):
            ctk.CTkLabel(
                footer, text="Bonus ya reclamado hoy — vuelve mañana",
                font=("Segoe UI", 12), text_color=THEME["ghost"],
            ).pack(side="left")
        else:
            ctk.CTkLabel(
                footer, text="Completa las 3 misiones para desbloquear el bonus",
                font=("Segoe UI", 11), text_color=THEME["muted"],
            ).pack(side="left")
        ctk.CTkButton(
            footer, text="Cerrar", width=90, height=32,
            fg_color=THEME["surface2"], hover_color=THEME["panel"],
            border_width=1, border_color=THEME["border"], text_color=THEME["text"],
            command=win.destroy,
        ).pack(side="right")
