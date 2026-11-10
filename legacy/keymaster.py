"""
KeyMaster // ORBITAL TRAINER
SpaceX-Cyberpunk · contratos · onboarding · FSRS · mini leccion · checklist · errores 2.3.
"""
import customtkinter as ctk
import time
from sound_engine import SoundEngine
from profile_manager import PlayerProfile
from content_generator import ContentGenerator
from tips_system import TipsSystem
from constructor_mode import ConstructorMixin
try:
    from contracts_ui import ContractsUIMixin
except Exception:
    class ContractsUIMixin:
        def _build_contracts_chip(self, parent):
            self.lbl_contracts = ctk.CTkLabel(parent, text="Contratos 0/3", font=("Segoe UI", 12), text_color=THEME["amber"])
            self.lbl_contracts.pack(anchor="e")
        def _refresh_contracts_label(self):
            pass
        def _show_contracts_panel(self):
            pass
        def _toast_contract(self, message, color=None):
            try:
                self.lbl_feedback.configure(text=str(message))
            except Exception:
                pass
try:
    from ollama_tutor import get_tutor
except Exception:
    get_tutor = None
try:
    from splash_screen import show_splash
except Exception:
    show_splash = None
try:
    from onboarding import OnboardingDialog, needs_onboarding, apply_onboarding_result
except Exception:
    OnboardingDialog = None
    def needs_onboarding(player):
        return False
    def apply_onboarding_result(player, result):
        pass
try:
    from fsrs_banner import FsrsBannerMixin
except Exception:
    class FsrsBannerMixin:
        def _build_fsrs_banner(self, parent):
            pass
        def _refresh_fsrs_banner(self, force=False):
            pass
        def _maybe_show_fsrs_banner(self):
            pass
try:
    from mini_lesson import build_mini_lesson
except Exception:
    def build_mini_lesson(*args, **kwargs):
        return {"title": "", "body": "", "example": "", "compact": "", "concept": ""}
try:
    from path_checklist_ui import PathChecklistMixin
except Exception:
    class PathChecklistMixin:
        def _build_path_checklist_widgets(self, path_frame):
            pass
        def _refresh_path_checklist(self):
            pass
        def _show_path_checklist(self):
            pass
try:
    from error_classifier import classify_typing_error, format_feedback
except Exception:
    def classify_typing_error(user, target):
        return {"category": "other", "message": "error", "position": -1, "expected": "", "got": ""}
    def format_feedback(info):
        return (info.get("message") or "error", "#FF3355")

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

THEME = {
    "bg": "#05070B", "surface": "#0B1018", "surface2": "#111827", "panel": "#0E1522",
    "border": "#1E2A3A", "cyan": "#00E5FF", "cyan_dim": "#00A8B8", "magenta": "#FF2BD6",
    "magenta_dim": "#B01A96", "amber": "#FFB020", "lime": "#39FF14", "red": "#FF3355",
    "red_dim": "#C91838", "violet": "#A855F7", "violet_dim": "#7C3AED",
    "text": "#E8F1FF", "muted": "#6B7C93", "ghost": "#3A4A5C",
}

class KeyMasterApp(PathChecklistMixin, FsrsBannerMixin, ContractsUIMixin, ConstructorMixin, ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("KeyMaster // ORBITAL TRAINER")
        self.geometry("1180x780")
        self.configure(fg_color=THEME["bg"])
        self.player = PlayerProfile()
        self.content = ContentGenerator()
        self.audio = SoundEngine()
        self.tips = TipsSystem()
        self.mode = "TRAINING"
        self.current_learning_path = getattr(self.player, "current_learning_path", "basics")
        self.current_code_category = "basic_functions"
        self.lives = 3
        self.survival_score = 0
        self.survival_difficulty = 1
        self.combo = 0
        self.current_challenge = None
        self.current_text = ""
        self.start_time = 0
        self.is_typing = False
        self.last_len = 0
        self.error_count = 0
        self._pending_explanation = ""
        self._builder_exercise = None
        self._builder_revealed = 0
        self._builder_used_scaffold = False
        self._builder_used_reveal = False
        self._builder_used_solution = False
        self.use_ai = False
        self.tutor = None
        self._stats_win = None
        self._lesson_seen = set()
        self._last_error_info = None
        if get_tutor:
            try:
                self.tutor = get_tutor(force_refresh=True)
            except Exception:
                self.tutor = None
        self._build_ui()
        self._set_mode("TRAINING")
        try:
            self.player.ensure_daily_contracts()
            self._refresh_contracts_label()
        except Exception:
            pass
        try:
            if needs_onboarding(self.player):
                self.after(300, self._run_onboarding)
            else:
                self.after(500, self._maybe_show_fsrs_banner)
        except Exception:
            pass

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=8)
        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left")
        self.lbl_level = ctk.CTkLabel(left, text="LVL 1", font=("Segoe UI", 24, "bold"), text_color=THEME["cyan"])
        self.lbl_level.pack(anchor="w")
        self.lbl_rank = ctk.CTkLabel(left, text="Novato", font=("Segoe UI", 12), text_color=THEME["muted"])
        self.lbl_rank.pack(anchor="w")
        self.mode_panel = ctk.CTkSegmentedButton(
            header, values=["ENTRENAMIENTO", "APRENDIZAJE", "CONSTRUCTOR", "SUPERVIVENCIA", "DIARIO"],
            command=self._on_mode, font=("Segoe UI", 11, "bold"),
            fg_color=THEME["surface"], selected_color=THEME["cyan_dim"], selected_hover_color=THEME["cyan"],
            unselected_color=THEME["surface2"], unselected_hover_color=THEME["panel"], text_color=THEME["text"])
        self.mode_panel.set("ENTRENAMIENTO")
        self.mode_panel.pack(side="top", pady=4)
        ai_row = ctk.CTkFrame(header, fg_color="transparent")
        ai_row.pack(side="top", pady=(2, 0))
        self.ai_switch = ctk.CTkSwitch(ai_row, text="IA local", command=self._toggle_ai, font=("Segoe UI", 11),
            progress_color=THEME["cyan"], button_color=THEME["cyan"], button_hover_color=THEME["magenta"], text_color=THEME["text"])
        self.ai_switch.pack(side="left", padx=4)
        self.lbl_ai = ctk.CTkLabel(ai_row, text="Ollama offline", font=("Segoe UI", 11), text_color=THEME["ghost"])
        self.lbl_ai.pack(side="left", padx=4)
        self.model_menu = ctk.CTkOptionMenu(ai_row, values=["(sin modelos)"], command=self._on_model_change, width=140, height=24, font=("Segoe UI", 10),
            fg_color=THEME["surface2"], button_color=THEME["cyan_dim"], button_hover_color=THEME["cyan"], text_color=THEME["text"],
            dropdown_fg_color=THEME["panel"], dropdown_hover_color=THEME["surface2"], dropdown_text_color=THEME["text"])
        self.model_menu.pack(side="left", padx=4)
        self.model_menu.configure(state="disabled")
        self.adaptive_switch = ctk.CTkSwitch(ai_row, text="Adaptativo", command=self._toggle_adaptive, font=("Segoe UI", 11),
            progress_color=THEME["magenta"], button_color=THEME["magenta"], button_hover_color=THEME["cyan"], text_color=THEME["text"])
        self.adaptive_switch.select()
        self.adaptive_switch.pack(side="left", padx=4)
        ctk.CTkLabel(ai_row, text="Ratio IA", font=("Segoe UI", 10), text_color=THEME["muted"]).pack(side="left", padx=(8, 2))
        self.ratio_slider = ctk.CTkSlider(ai_row, from_=0, to=100, number_of_steps=20, command=self._on_ratio_change, width=90, height=16,
            progress_color=THEME["cyan"], button_color=THEME["cyan"], button_hover_color=THEME["magenta"], fg_color=THEME["surface2"])
        self.ratio_slider.set(55)
        self.ratio_slider.pack(side="left", padx=2)
        self.lbl_ratio = ctk.CTkLabel(ai_row, text="55%", font=("Segoe UI", 10, "bold"), text_color=THEME["cyan"], width=36)
        self.lbl_ratio.pack(side="left")
        self._refresh_ai_status()
        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right")
        self.lbl_combo = ctk.CTkLabel(right, text="", font=("Segoe UI", 18, "bold"), text_color=THEME["magenta"])
        self.lbl_combo.pack(anchor="e")
        self._build_contracts_chip(right)
        self.lbl_wpm = ctk.CTkLabel(right, text="WPM: 0", font=("Segoe UI", 14), text_color=THEME["text"])
        self.lbl_wpm.pack(anchor="e")
        pw = ctk.CTkFrame(right, fg_color="transparent")
        pw.pack(anchor="e", pady=4)
        self.btn_hint = ctk.CTkButton(pw, text="Pista", width=70, height=28, command=lambda: self._power("hint"),
            fg_color=THEME["surface2"], hover_color=THEME["violet_dim"], border_width=1, border_color=THEME["violet"], text_color=THEME["text"], corner_radius=6)
        self.btn_hint.pack(side="left", padx=2)
        self.btn_skip = ctk.CTkButton(pw, text="Saltar", width=70, height=28, command=lambda: self._power("skip"),
            fg_color=THEME["surface2"], hover_color=THEME["cyan_dim"], border_width=1, border_color=THEME["cyan"], text_color=THEME["text"], corner_radius=6)
        self.btn_skip.pack(side="left", padx=2)
        self.btn_stats = ctk.CTkButton(pw, text="Stats", width=70, height=28, command=self._show_stats,
            fg_color=THEME["surface2"], hover_color=THEME["magenta_dim"], border_width=1, border_color=THEME["magenta"], text_color=THEME["text"], corner_radius=6)
        self.btn_stats.pack(side="left", padx=2)
        self.area = ctk.CTkScrollableFrame(self, fg_color="transparent", scrollbar_button_color=THEME["cyan_dim"], scrollbar_button_hover_color=THEME["cyan"])
        self.area.grid(row=1, column=0, sticky="nsew", padx=20, pady=8)
        self.path_frame = ctk.CTkFrame(self.area, fg_color=THEME["panel"], corner_radius=12, border_width=1, border_color=THEME["cyan_dim"])
        ctk.CTkLabel(self.path_frame, text="◈ RUTA DE APRENDIZAJE", font=("Segoe UI", 13, "bold"), text_color=THEME["cyan"]).pack(pady=(8, 4))
        self.path_selector = ctk.CTkOptionMenu(self.path_frame, values=self.content.get_available_paths(), command=self._on_path_change, font=("Segoe UI", 12),
            fg_color=THEME["surface2"], button_color=THEME["cyan_dim"], button_hover_color=THEME["cyan"], text_color=THEME["text"],
            dropdown_fg_color=THEME["panel"], dropdown_hover_color=THEME["surface2"], dropdown_text_color=THEME["text"])
        self.path_selector.set(self.current_learning_path)
        self.path_selector.pack(pady=(0, 4), padx=10)
        try:
            self._build_path_checklist_widgets(self.path_frame)
        except Exception:
            pass
        self.cat_frame = ctk.CTkFrame(self.area, fg_color=THEME["panel"], corner_radius=12, border_width=1, border_color=THEME["magenta_dim"])
        ctk.CTkLabel(self.cat_frame, text="◈ CATEGORIA DE CODIGO", font=("Segoe UI", 13, "bold"), text_color=THEME["magenta"]).pack(pady=(8, 4))
        cats = self.content.get_code_builder_categories()
        self.cat_selector = ctk.CTkOptionMenu(self.cat_frame, values=cats, command=self._on_category_change, font=("Segoe UI", 12),
            fg_color=THEME["surface2"], button_color=THEME["magenta_dim"], button_hover_color=THEME["magenta"], text_color=THEME["text"],
            dropdown_fg_color=THEME["panel"], dropdown_hover_color=THEME["surface2"], dropdown_text_color=THEME["text"])
        if cats:
            self.cat_selector.set(cats[0])
            self.current_code_category = cats[0]
        self.cat_selector.pack(pady=(0, 8), padx=10)
        self._build_fsrs_banner(self.area)
        self.lbl_diff = ctk.CTkLabel(self.area, text="", font=("Consolas", 12), text_color=THEME["ghost"])
        self.lbl_diff.pack(pady=(12, 4))
        self.lbl_concept = ctk.CTkLabel(self.area, text="", font=("Segoe UI", 11), text_color=THEME["muted"])
        self.lbl_concept.pack()
        self.lbl_desc = ctk.CTkLabel(self.area, text="", font=("Segoe UI", 13), text_color=THEME["muted"], wraplength=850)
        self.lbl_target = ctk.CTkLabel(self.area, text="...", font=("JetBrains Mono", 26, "bold"), wraplength=900, text_color=THEME["text"])
        self.lbl_target.pack(pady=12)
        self.lbl_tip = ctk.CTkLabel(self.area, text="", font=("Segoe UI", 12), text_color=THEME["amber"], wraplength=850)
        self.lbl_hint = ctk.CTkLabel(self.area, text="", font=("Segoe UI", 12), text_color=THEME["cyan"], wraplength=850)
        self.entry_var = ctk.StringVar()
        self.entry_var.trace_add("write", self._on_type)
        self.entry = ctk.CTkEntry(self.area, textvariable=self.entry_var, width=720, height=56, font=("JetBrains Mono", 22), justify="center", corner_radius=10, border_width=2,
            fg_color=THEME["surface"], border_color=THEME["cyan_dim"], text_color=THEME["cyan"], placeholder_text_color=THEME["ghost"])
        self.entry.pack(pady=12)
        self.code_textbox = ctk.CTkTextbox(self.area, width=780, height=260, font=("JetBrains Mono", 14), corner_radius=10, border_width=2, wrap="none",
            fg_color=THEME["surface"], border_color=THEME["cyan_dim"], text_color=THEME["text"])
        self.code_textbox.bind("<Control-Return>", lambda e: self._verify_code())
        self.lbl_feedback = ctk.CTkLabel(self.area, text="// SISTEMA LISTO — escribe para iniciar", font=("Segoe UI", 14), text_color=THEME["muted"])
        self.lbl_feedback.pack(pady=4)
        self.btn_verify = ctk.CTkButton(self.area, text="⚡ VERIFICAR  ·  Ctrl+Enter", command=self._verify_code,
            fg_color=THEME["lime"], hover_color="#2BD910", font=("Segoe UI", 14, "bold"), height=44, width=300, border_width=2, border_color=THEME["lime"], text_color=THEME["bg"], corner_radius=8)
        self.builder_btns = ctk.CTkFrame(self.area, fg_color="transparent")
        self.btn_scaffold = ctk.CTkButton(self.builder_btns, text="Scaffold", width=100, height=32, command=self._load_scaffold, fg_color=THEME["cyan_dim"], hover_color=THEME["cyan"], border_width=1, border_color=THEME["cyan"], text_color=THEME["bg"], font=("Segoe UI", 12, "bold"), corner_radius=8)
        self.btn_scaffold.pack(side="left", padx=4)
        self.btn_reveal = ctk.CTkButton(self.builder_btns, text="Revelar linea", width=120, height=32, command=self._reveal_line, fg_color=THEME["violet_dim"], hover_color=THEME["violet"], border_width=1, border_color=THEME["violet"], text_color=THEME["text"], font=("Segoe UI", 12, "bold"), corner_radius=8)
        self.btn_reveal.pack(side="left", padx=4)
        self.btn_solution = ctk.CTkButton(self.builder_btns, text="Ver solucion", width=120, height=32, command=self._show_solution, fg_color=THEME["red_dim"], hover_color=THEME["red"], border_width=1, border_color=THEME["red"], text_color=THEME["text"], font=("Segoe UI", 12, "bold"), corner_radius=8)
        self.btn_solution.pack(side="left", padx=4)
        self.btn_ai_hint = ctk.CTkButton(self.builder_btns, text="Tutor IA", width=100, height=32, command=self._ai_builder_hint, fg_color=THEME["magenta_dim"], hover_color=THEME["magenta"], border_width=1, border_color=THEME["magenta"], text_color=THEME["text"], font=("Segoe UI", 12, "bold"), corner_radius=8)
        self.btn_ai_hint.pack(side="left", padx=4)
        self.btn_next_ex = ctk.CTkButton(self.builder_btns, text="Siguiente", width=100, height=32, command=self._new_code_builder_exercise, fg_color=THEME["surface2"], hover_color=THEME["panel"], border_width=1, border_color=THEME["border"], text_color=THEME["text"], font=("Segoe UI", 12, "bold"), corner_radius=8)
        self.btn_next_ex.pack(side="left", padx=4)
        self.progress = ctk.CTkProgressBar(self, height=10, progress_color=THEME["cyan"], fg_color=THEME["surface2"], corner_radius=4)
        self.progress.grid(row=2, column=0, sticky="ew")
        self.entry.focus()

    def _on_mode(self, value):
        m = {"ENTRENAMIENTO": "TRAINING", "APRENDIZAJE": "LEARNING", "CONSTRUCTOR": "CODE_BUILDER", "SUPERVIVENCIA": "SURVIVAL", "DIARIO": "DAILY"}
        self._set_mode(m.get(value, "TRAINING"))

    def _on_path_change(self, path):
        self.current_learning_path = path
        try:
            self.player.current_learning_path = path
            self.player.save_profile()
        except Exception:
            pass
        try:
            self._refresh_path_checklist()
        except Exception:
            pass
        self._new_challenge()

    def _on_category_change(self, category):
        self.current_code_category = category
        self._new_code_builder_exercise()

    def _set_mode(self, mode):
        self.mode = mode
        self.combo = 0
        self.lives = 3
        self.lbl_combo.configure(text="")
        self.path_frame.pack_forget()
        self.cat_frame.pack_forget()
        self.lbl_desc.pack_forget()
        self.lbl_tip.pack_forget()
        self.lbl_hint.pack_forget()
        self.code_textbox.pack_forget()
        self.btn_verify.pack_forget()
        try:
            self.builder_btns.pack_forget()
        except Exception:
            pass
        self.entry.pack_forget()
        self.lbl_target.pack_forget()
        if mode == "TRAINING":
            self.lbl_level.configure(text=f"LVL {self.player.level}")
            self.lbl_rank.configure(text=self.player.rank)
            self.lbl_target.pack(pady=12)
            self.entry.pack(pady=12)
            self._new_challenge()
            self.entry.focus()
        elif mode == "LEARNING":
            self.path_frame.pack(pady=(4, 8))
            self.lbl_level.configure(text=f"LVL {self.player.level}")
            self.lbl_rank.configure(text=self.player.rank)
            try:
                self._refresh_path_checklist()
            except Exception:
                pass
            self.lbl_target.pack(pady=12)
            self.entry.pack(pady=12)
            self._new_challenge()
            self.entry.focus()
        elif mode == "CODE_BUILDER":
            self._start_code_builder()
        elif mode == "SURVIVAL":
            self.survival_score = 0
            self.survival_difficulty = 1
            self.lbl_level.configure(text="SCORE 0")
            self.lbl_rank.configure(text=f"Vidas: {self.lives}")
            self.lbl_target.pack(pady=12)
            self.entry.pack(pady=12)
            self._new_challenge()
            self.entry.focus()
        else:
            self.lbl_level.configure(text="DIARIO")
            self.lbl_rank.configure(text=f"Racha: {getattr(self.player, 'daily_streak', 0)}")
            self.lbl_target.pack(pady=12)
            self.entry.pack(pady=12)
            self._new_challenge()
            self.entry.focus()

    def _new_challenge(self):
        self._sync_learner_context()
        if self.mode == "CODE_BUILDER":
            self._new_code_builder_exercise()
            return
        if self.mode == "TRAINING":
            diff = min(10, max(1, self.player.level // 2 or 1))
            self.current_challenge = self.content.get_challenge(diff)
        elif self.mode == "LEARNING":
            diff = min(8, 2 + self.player.level // 3)
            self.current_challenge = self.content.get_challenge(diff, self.current_learning_path, prefer_blank=True)
        elif self.mode == "SURVIVAL":
            self.current_challenge = self.content.get_challenge(self.survival_difficulty)
        else:
            dailies = self.content.get_daily_challenges()
            self.current_challenge = dailies[0] if dailies else self.content.get_challenge(3)
        self._show_challenge()

    def _show_challenge(self):
        ch = self.current_challenge
        if not ch:
            return
        self.current_text = ch.text
        self.error_count = 0
        self.last_len = 0
        self.is_typing = False
        self.start_time = 0
        display = self.content.get_challenge_display_text(ch)
        is_blank = getattr(ch, "challenge_type", "full") == "blank"
        if is_blank:
            self.lbl_target.configure(text=display, text_color=THEME["amber"])
            self.lbl_feedback.configure(text="Completa el hueco ____", text_color=THEME["amber"])
        else:
            self.lbl_target.configure(text=display, text_color=THEME["text"])
            self.lbl_feedback.configure(text="Escribe el codigo", text_color=THEME["muted"])
        self.lbl_diff.configure(text=f"Nivel {ch.difficulty} | {ch.category}")
        concept = getattr(ch, "concept", "") or ""
        self.lbl_concept.configure(text=f"Concepto: {concept}" if self.mode in ("LEARNING", "TRAINING") and concept else "")
        self.lbl_hint.configure(text="")
        self.lbl_hint.pack_forget()
        try:
            self._show_mini_lesson(ch)
        except Exception:
            try:
                self.lbl_tip.pack_forget()
                self.lbl_desc.pack_forget()
            except Exception:
                pass
        self.entry_var.set("")
        self.entry.configure(border_color=THEME["cyan_dim"])

    def _show_mini_lesson(self, ch):
        if self.mode not in ("LEARNING", "TRAINING", "DAILY"):
            self.lbl_tip.pack_forget()
            self.lbl_desc.pack_forget()
            return
        concept = getattr(ch, "concept", "") or ""
        lesson = build_mini_lesson(challenge=ch, concept=concept, tips_system=getattr(self, "tips", None), content=getattr(self, "content", None))
        seen = getattr(self, "_lesson_seen", set())
        first_time = concept and concept not in seen
        if concept:
            seen.add(concept)
            self._lesson_seen = seen
        if self.mode == "LEARNING" or first_time:
            title = lesson.get("title") or "◈ MINI LECCION"
            body = lesson.get("body") or ""
            example = lesson.get("example") or ""
            text = f"{body}\n{example}" if example and body else (body or example)
            self.lbl_tip.configure(text=title, text_color=THEME["cyan"])
            self.lbl_desc.configure(text=text, text_color=THEME["muted"])
            try:
                self.lbl_tip.pack(before=self.lbl_target, pady=(4, 0))
                self.lbl_desc.pack(before=self.lbl_target, pady=(2, 6))
            except Exception:
                self.lbl_tip.pack(pady=(4, 0))
                self.lbl_desc.pack(pady=(2, 6))
            self.lbl_feedback.configure(text="Lee la mini leccion · luego escribe el reto", text_color=THEME["cyan"])
        else:
            compact = lesson.get("compact") or lesson.get("body") or ""
            if compact:
                self.lbl_tip.configure(text=f"💡 {compact[:140]}", text_color=THEME["amber"])
                try:
                    self.lbl_tip.pack(before=self.lbl_target, pady=(2, 4))
                except Exception:
                    self.lbl_tip.pack(pady=(2, 4))
            else:
                self.lbl_tip.pack_forget()
            self.lbl_desc.pack_forget()

    def _on_type(self, *args):
        if self.mode == "CODE_BUILDER":
            return
        text = self.entry_var.get()
        target = self.current_text
        if not self.is_typing and text:
            self.is_typing = True
            self.start_time = time.time()
        if len(text) > self.last_len:
            if target.startswith(text):
                try:
                    self.audio.play_click()
                except Exception:
                    pass
                self.entry.configure(border_color=THEME["lime"])
            else:
                self.error_count += 1
                try:
                    self.audio.play_error()
                except Exception:
                    pass
                self.entry.configure(border_color=THEME["red"])
                try:
                    info = classify_typing_error(text, target)
                    self._last_error_info = info
                    fb, color = format_feedback(info)
                    self.lbl_feedback.configure(text=fb, text_color=color)
                    if self.current_challenge and hasattr(self.player, "record_error_class"):
                        self.player.record_error_class(
                            getattr(self.current_challenge, "concept", "") or "",
                            info.get("category", "other"),
                        )
                except Exception:
                    pass
                if self.mode == "SURVIVAL":
                    self.lives -= 1
                    self.combo = 0
                    self.lbl_rank.configure(text=f"Vidas: {self.lives}")
                    try:
                        if self.current_challenge:
                            self.player.record_concept_fail(self.current_challenge.concept, errors=1)
                    except Exception:
                        pass
                    if self.lives <= 0:
                        self.lbl_feedback.configure(text="Game Over", text_color=THEME["red"])
                        try:
                            self.audio.play_gameover()
                        except Exception:
                            pass
                        self.after(1500, lambda: self._set_mode("SURVIVAL"))
                        self.last_len = len(text)
                        return
        self.last_len = len(text)
        if text == target and target:
            self._success()

    def _success(self):
        duration = max(0.001, time.time() - self.start_time)
        words = max(1, len(self.current_text.split()))
        wpm = int((words / duration) * 60)
        perfect = self.error_count == 0
        self.lbl_wpm.configure(text=f"WPM: {wpm}")
        self.combo = self.combo + 1 if perfect else 0
        self.lbl_combo.configure(text=f"x{self.combo}" if self.combo > 1 else "")
        concept = self.current_challenge.concept if self.current_challenge else ""
        try:
            self.player.record_challenge_completion(wpm, self.error_count, len(self.current_text), concept, perfect)
        except Exception:
            pass
        try:
            just = []
            if self.mode == "TRAINING":
                just = self.player.bump_contract("training_ok", 1)
            elif self.mode == "LEARNING":
                just = self.player.bump_contract("learning_ok", 1)
                is_blank = getattr(self.current_challenge, "challenge_type", "full") == "blank"
                if is_blank and perfect:
                    just = list(just) + list(self.player.bump_contract("blank_perfect", 1) or [])
                try:
                    due = set(self.player.get_due_concepts(limit=20))
                    if concept and concept in due:
                        just = list(just) + list(self.player.bump_contract("due_review", 1) or [])
                except Exception:
                    pass
            elif self.mode == "SURVIVAL":
                just = self.player.bump_contract("survival_score", getattr(self, "survival_score", 0))
            if just:
                labels = ", ".join((c.get("label") or c.get("id", "?"))[:48] for c in just)
                self._toast_contract(f"◆ Contrato listo: {labels}", THEME["amber"])
            self._refresh_contracts_label()
            try:
                self._refresh_fsrs_banner()
            except Exception:
                pass
            try:
                if self.mode == "LEARNING":
                    self._refresh_path_checklist()
            except Exception:
                pass
        except Exception:
            pass
        exp = self.content.get_explanation(concept, self.current_challenge)
        self._pending_explanation = exp or ""
        if self.mode == "TRAINING":
            base = 10 + len(self.current_text)
            total = int(base * (1 + 0.1 * max(0, self.combo - 1)))
            leveled = self.player.add_xp(total)
            self.lbl_feedback.configure(text=f"+{total} XP", text_color=THEME["lime"])
            self.lbl_level.configure(text=f"LVL {self.player.level}")
            self.lbl_rank.configure(text=self.player.rank)
            if leveled:
                try:
                    self.audio.play_levelup()
                except Exception:
                    pass
            need = max(1, self.player.xp_for_next_level)
            self.progress.set(min(1.0, self.player.xp / need))
        elif self.mode == "LEARNING":
            base = 15 + len(self.current_text)
            if getattr(self.current_challenge, "challenge_type", "full") == "blank":
                base += 5
            self.player.add_xp(base)
            self.lbl_feedback.configure(text=f"+{base} XP (aprendizaje)", text_color=THEME["cyan"])
        elif self.mode == "SURVIVAL":
            self.survival_score += 10 + self.survival_difficulty
            if self.combo and self.combo % 5 == 0:
                self.survival_difficulty = min(12, self.survival_difficulty + 1)
            self.lbl_level.configure(text=f"SCORE {self.survival_score}")
            self.lbl_feedback.configure(text="OK", text_color=THEME["lime"])
        else:
            self.lbl_feedback.configure(text="Desafio diario OK", text_color=THEME["amber"])
        if self._pending_explanation:
            self.lbl_hint.configure(text=f"📖 {self._pending_explanation}")
            self._pack_hint_label()
        self.after(1200, self._new_challenge)

    def _pack_hint_label(self):
        """Coloca la pista sobre el widget de entrada activo (entry o editor del Constructor)."""
        anchor = None
        for w in (self.entry, self.code_textbox, self.btn_verify):
            try:
                if w.winfo_manager() == "pack":
                    anchor = w
                    break
            except Exception:
                pass
        try:
            if anchor is not None:
                self.lbl_hint.pack(before=anchor, pady=(0, 8))
            else:
                self.lbl_hint.pack(pady=(0, 8))
        except Exception:
            self.lbl_hint.pack(pady=(0, 8))

    def _power(self, kind):
        try:
            ok = self.player.use_powerup(kind)
        except Exception:
            ok = False
        if not ok:
            self.lbl_feedback.configure(text="Sin power-up", text_color=THEME["red"])
            return
        try:
            self.audio.play_powerup()
        except Exception:
            pass
        if kind == "hint" and self.mode == "CODE_BUILDER":
            ex = getattr(self, "_builder_exercise", None) or {}
            parts = [f"💡 {ex.get('description') or 'Construye el ejercicio bloque a bloque'}"]
            try:
                struct = self.content.get_code_builder_structure_hint(ex)
                if struct:
                    parts.append(f"🧩 {struct}")
            except Exception:
                pass
            self.lbl_hint.configure(text="\n".join(parts))
            self._pack_hint_label()
        elif kind == "hint" and self.current_challenge:
            parts = [f"💡 {self.current_challenge.hint or 'Sigue el patron'}"]
            exp = self.content.get_explanation(self.current_challenge.concept, self.current_challenge)
            if exp:
                parts.append(f"📖 {exp}")
            self.lbl_hint.configure(text="\n".join(parts))
            self._pack_hint_label()
        elif kind == "skip":
            self.after(200, self._new_code_builder_exercise if self.mode == "CODE_BUILDER" else self._new_challenge)

    def _refresh_ai_status(self):
        if not get_tutor:
            self.lbl_ai.configure(text="Modulo ollama no cargado", text_color=THEME["ghost"])
            return
        try:
            if self.tutor is None:
                self.tutor = get_tutor(force_refresh=True)
            else:
                self.tutor.refresh()
            if self.tutor.is_available():
                models = self.tutor.list_models() or [self.tutor.model or "?"]
                self.model_menu.configure(values=models, state="normal")
                current = self.tutor.model or models[0]
                if current not in models:
                    current = models[0]
                    self.tutor.set_model(current)
                self.model_menu.set(current)
                self.lbl_ai.configure(text="online", text_color=THEME["lime"])
            else:
                self.lbl_ai.configure(text="offline", text_color=THEME["ghost"])
                self.model_menu.configure(values=["(sin modelos)"], state="disabled")
        except Exception:
            self.lbl_ai.configure(text="offline", text_color=THEME["ghost"])

    def _on_model_change(self, name: str):
        if not self.tutor or not name or name.startswith("("):
            return
        ok = self.tutor.set_model(name)
        self.lbl_feedback.configure(text=f"Modelo: {self.tutor.model}" if ok else f"No se pudo seleccionar {name}", text_color=THEME["lime"] if ok else THEME["red"])

    def _on_ratio_change(self, value):
        pct = int(round(float(value)))
        self.lbl_ratio.configure(text=f"{pct}%")
        self.content.set_ai_ratio(pct / 100.0)

    def _toggle_adaptive(self):
        self.content.set_adaptive(bool(self.adaptive_switch.get()))
        self._sync_learner_context()

    def _sync_learner_context(self):
        try:
            weak = self.player.get_weak_concepts(limit=6)
        except Exception:
            weak = []
        try:
            due = self.player.get_due_concepts(limit=8)
        except Exception:
            due = []
        self.content.set_learner_context(weak_concepts=weak, level=self.player.level, due_concepts=due)

    def _toggle_ai(self):
        self.use_ai = bool(self.ai_switch.get())
        self._refresh_ai_status()
        if self.use_ai:
            if not self.tutor or not self.tutor.is_available():
                self.use_ai = False
                self.ai_switch.deselect()
                self.lbl_feedback.configure(text="Ollama no responde", text_color=THEME["amber"])
                return
            self.content.set_ai(True, self.tutor)
            self.content.set_ai_ratio(float(self.ratio_slider.get()) / 100.0)
            self.content.set_adaptive(bool(self.adaptive_switch.get()))
            self._sync_learner_context()
            self.lbl_feedback.configure(text=f"IA activa · {self.tutor.model}", text_color=THEME["lime"])
        else:
            self.content.set_ai(False, self.tutor)
            self.lbl_feedback.configure(text="IA desactivada", text_color=THEME["muted"])

    def _run_onboarding(self):
        if OnboardingDialog is None:
            return
        try:
            paths = list(self.content.get_available_paths() or ["basics"])
        except Exception:
            paths = ["basics"]
        def _done(result):
            try:
                apply_onboarding_result(self.player, result)
            except Exception:
                try:
                    self.player.onboarding_done = True
                    self.player.save_profile()
                except Exception:
                    pass
            if result:
                path = result.get("path") or "basics"
                self.current_learning_path = path
                try:
                    self.path_selector.set(path)
                except Exception:
                    pass
                self.lbl_level.configure(text=f"LVL {self.player.level}")
                self.lbl_rank.configure(text=self.player.rank)
                try:
                    self.mode_panel.set("APRENDIZAJE")
                except Exception:
                    pass
                self._set_mode("LEARNING")
                self.after(800, self._maybe_show_fsrs_banner)
        OnboardingDialog(self, available_paths=paths, on_done=_done)

    def _show_stats(self):
        win = ctk.CTkToplevel(self)
        self._stats_win = win
        win.title("KeyMaster // TELEMETRIA")
        win.geometry("520x480")
        win.configure(fg_color=THEME["bg"])
        ctk.CTkLabel(win, text="◈ TELEMETRIA ORBITAL", font=("Segoe UI", 18, "bold"), text_color=THEME["cyan"]).pack(pady=(16, 4))
        try:
            summary = self.player.get_stats_summary()
        except Exception:
            summary = {"level": self.player.level, "xp": self.player.xp, "rank": getattr(self.player, "rank", "?")}
        card = ctk.CTkFrame(win, fg_color=THEME["panel"], corner_radius=12, border_width=1, border_color=THEME["cyan_dim"])
        card.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(card, text=f"LVL {summary.get('level')}  ·  XP {summary.get('xp')}  ·  {summary.get('rank')}", font=("Segoe UI", 14), text_color=THEME["text"]).pack(pady=12)
        try:
            br = self.player.get_error_breakdown() if hasattr(self.player, "get_error_breakdown") else {}
            if br:
                top = sorted(br.items(), key=lambda x: -x[1])[:5]
                line = " · ".join(f"{k}:{v}" for k, v in top)
                ctk.CTkLabel(card, text=f"Errores: {line}", font=("Segoe UI", 11), text_color=THEME["amber"]).pack(pady=(0, 8))
        except Exception:
            pass
        ctk.CTkButton(win, text="Checklist de ruta", width=180, height=32, command=lambda: (win.destroy(), self._show_path_checklist()),
            fg_color=THEME["cyan_dim"], hover_color=THEME["cyan"], text_color=THEME["bg"], font=("Segoe UI", 12, "bold")).pack(pady=4)
        ctk.CTkButton(win, text="Ver contratos del dia", width=180, height=32, command=lambda: (win.destroy(), self._show_contracts_panel()),
            fg_color=THEME["amber"], hover_color="#E09A10", text_color=THEME["bg"], font=("Segoe UI", 12, "bold")).pack(pady=4)
        ctk.CTkButton(win, text="Cerrar", width=120, height=32, command=win.destroy,
            fg_color=THEME["surface2"], hover_color=THEME["panel"], border_width=1, border_color=THEME["border"], text_color=THEME["text"]).pack(pady=(8, 16))


if __name__ == "__main__":
    app = KeyMasterApp()
    if show_splash:
        try:
            show_splash(app)
        except Exception:
            pass
    app.mainloop()
