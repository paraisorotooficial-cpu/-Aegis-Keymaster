try:
    from error_classifier import classify_constructor_error, format_feedback
except Exception:
    def classify_constructor_error(**kwargs):
        return {"category": "other", "message": "error"}
    def format_feedback(info):
        return (info.get("message") or "error", "#FF3355")

"""Constructor mode helpers for KeyMaster Pro."""
import ast
import io
import contextlib


class ConstructorMixin:
    """Mixin with Code Builder (Constructor) mode methods."""

    def _start_code_builder(self):
        self.cat_frame.pack(pady=(4, 8))
        self.path_frame.pack_forget()
        self.lbl_target.pack_forget()
        self.entry.pack_forget()
        self.lbl_desc.pack(pady=(4, 4))
        self.lbl_tip.pack(pady=(0, 6))
        self.code_textbox.pack(pady=12)
        self.btn_verify.pack(pady=6)
        self.builder_btns.pack(pady=4)
        self.lbl_level.configure(text=f"LVL {self.player.level}")
        self.lbl_rank.configure(text="Constructor")
        self._new_code_builder_exercise()

    def _new_code_builder_exercise(self):
        try:
            self._sync_learner_context()
        except Exception:
            pass
        diff = min(8, 2 + self.player.level // 3)
        exercise = self.content.get_code_builder_exercise(
            difficulty=diff, category=self.current_code_category
        )
        if not exercise:
            self.lbl_feedback.configure(text="Sin ejercicios en esta categoria", text_color="#FF3355")
            return
        self._builder_exercise = exercise
        self._builder_revealed = 0
        self._builder_used_scaffold = False
        self._builder_used_reveal = False
        self._builder_used_solution = False
        self._builder_passed_via_tests = False
        self.current_challenge = type("obj", (object,), {
            "text": exercise["code"],
            "difficulty": exercise["difficulty"],
            "concept": exercise.get("concept", ""),
            "title": exercise.get("title", ""),
            "description": exercise.get("description", ""),
            "hint": exercise.get("description", "Escribe el bloque completo"),
            "challenge_type": "full",
            "prompt": "",
            "explanation": "",
            "scaffold": exercise.get("scaffold", ""),
            "goals": exercise.get("goals", []),
        })()
        cat_name = self.content.get_category_name(self.current_code_category)
        self.lbl_diff.configure(text=f"Nivel {exercise['difficulty']} | {cat_name}")
        self.lbl_concept.configure(text=f"Concepto: {exercise.get('concept', '')}")
        self.lbl_desc.configure(text=exercise.get("description", ""))
        goals = exercise.get("goals") or []
        tip = self.content.get_code_builder_structure_hint(exercise)
        if goals:
            tip = tip + " | " + "; ".join(goals[:3])
        self.lbl_tip.configure(text=tip)
        self.lbl_hint.configure(text="")
        self.lbl_hint.pack_forget()
        self.code_textbox.delete("1.0", "end")
        self.code_textbox.configure(border_color="#1E2A3A")
        self._clear_diff_tags()
        self.lbl_feedback.configure(text="Escribe el codigo · Ctrl+Enter para verificar", text_color="#6B7C93")

    def _load_scaffold(self):
        if not self._builder_exercise:
            return
        sc = self._builder_exercise.get("scaffold") or ""
        if not sc:
            self.lbl_feedback.configure(text="Sin scaffold para este ejercicio", text_color="#FFB020")
            return
        self._builder_used_scaffold = True
        self.code_textbox.delete("1.0", "end")
        self.code_textbox.insert("1.0", sc)
        self._clear_diff_tags()
        self.lbl_feedback.configure(text="Scaffold cargado (-XP al completar)", text_color="#00E5FF")

    def _reveal_line(self):
        if not self._builder_exercise:
            return
        lines = (self._builder_exercise.get("code") or "").split("\n")
        if self._builder_revealed >= len(lines):
            self.lbl_feedback.configure(text="Ya no hay mas lineas", text_color="#FFB020")
            return
        self._builder_used_reveal = True
        line = lines[self._builder_revealed]
        self._builder_revealed += 1
        cur = self.code_textbox.get("1.0", "end-1c")
        if cur and not cur.endswith("\n"):
            cur += "\n"
        self.code_textbox.delete("1.0", "end")
        self.code_textbox.insert("1.0", cur + line + ("\n" if self._builder_revealed < len(lines) else ""))
        self._clear_diff_tags()
        self.lbl_feedback.configure(
            text=f"Revelada linea {self._builder_revealed}/{len(lines)}",
            text_color="#A855F7",
        )

    def _show_solution(self):
        if not self._builder_exercise:
            return
        self._builder_used_solution = True
        code = self._builder_exercise.get("code") or ""
        self.code_textbox.delete("1.0", "end")
        self.code_textbox.insert("1.0", code)
        self._clear_diff_tags()
        self.lbl_feedback.configure(text="Solucion visible (sin XP de maestria)", text_color="#FF3355")

    def _setup_diff_tags(self):
        try:
            tb = self.code_textbox._textbox
            tb.tag_configure("diff_ok", background="#0A1F14", foreground="#39FF14")
            tb.tag_configure("diff_bad", background="#2A0A12", foreground="#FF6B7A")
            tb.tag_configure("diff_extra", background="#1A1208", foreground="#FFB020")
        except Exception:
            pass

    def _clear_diff_tags(self):
        try:
            tb = self.code_textbox._textbox
            for tag in ("diff_ok", "diff_bad", "diff_extra"):
                tb.tag_remove(tag, "1.0", "end")
        except Exception:
            pass

    def _apply_line_diff(self, user_code: str, target_code: str) -> str:
        self._setup_diff_tags()
        self._clear_diff_tags()
        u_lines = user_code.split("\n")
        t_lines = target_code.split("\n")
        try:
            tb = self.code_textbox._textbox
        except Exception:
            return ""
        summary_parts = []
        for i in range(max(len(u_lines), len(t_lines))):
            start = f"{i+1}.0"
            end = f"{i+1}.end"
            if i < len(u_lines) and i < len(t_lines):
                if u_lines[i].rstrip() == t_lines[i].rstrip():
                    try:
                        tb.tag_add("diff_ok", start, end)
                    except Exception:
                        pass
                else:
                    try:
                        tb.tag_add("diff_bad", start, end)
                    except Exception:
                        pass
                    summary_parts.append(f"L{i+1}")
            elif i < len(u_lines):
                try:
                    tb.tag_add("diff_extra", start, end)
                except Exception:
                    pass
                summary_parts.append(f"L{i+1}+")
        summary = ", ".join(summary_parts[:6])
        if len(summary_parts) > 6:
            summary += "…"
        if summary:
            summary = "Difiere: " + summary
        summary += "  |  verde=ok  rojo=error  ambar=extra"
        return summary

    def _normalize_code(self, code: str) -> str:
        lines = []
        for line in code.splitlines():
            s = line.rstrip()
            if s.strip():
                lines.append(s)
        return "\n".join(lines)

    def _codes_equivalent(self, a: str, b: str) -> bool:
        return self._normalize_code(a) == self._normalize_code(b)

    def _run_exercise_tests(self, user_code, tests):
        ns = {}
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                exec(user_code, ns, ns)
        except Exception as e:
            return False, f"Runtime: {type(e).__name__}: {e}"
        out = buf.getvalue()
        for i, t in enumerate(tests, 1):
            try:
                if isinstance(t, str):
                    exec(t, ns, ns)
                elif isinstance(t, dict):
                    if "stdout_contains" in t:
                        assert t["stdout_contains"] in out, f"stdout sin {t['stdout_contains']!r}"
                    elif "var" in t:
                        name = t["var"]
                        assert name in ns, f"variable {name} no definida"
                        if "equals" in t:
                            assert ns[name] == t["equals"], f"{name}={ns[name]!r} != {t['equals']!r}"
            except Exception as e:
                return False, f"Test {i}/{len(tests)} error: {type(e).__name__}: {e}"
        return True, f"{len(tests)} tests OK"

    def _verify_code(self):
        if self.mode != "CODE_BUILDER" or not self.current_challenge:
            return
        user_code = self.code_textbox.get("1.0", "end-1c")
        target_code = self.current_challenge.text
        try:
            ast.parse(user_code)
        except SyntaxError as e:
            self.code_textbox.configure(border_color="#FF3355")
            try:
                info = classify_constructor_error(user_code=user_code, syntax_error=e)
                self._last_error_info = info
                fb, color = format_feedback(info)
                self.lbl_feedback.configure(text=fb, text_color=color)
                concept = (getattr(self, "_builder_exercise", None) or {}).get("concept", "")
                if hasattr(self.player, "record_error_class"):
                    self.player.record_error_class(concept, "syntax")
            except Exception:
                self.lbl_feedback.configure(
                    text=f"Error de sintaxis (linea {e.lineno}): {e.msg}",
                    text_color="#FF3355",
                )
            try:
                self._setup_diff_tags()
                self._clear_diff_tags()
                ln = e.lineno or 1
                tb = self.code_textbox._textbox
                tb.tag_add("diff_bad", f"{ln}.0", f"{ln}.end")
            except Exception:
                pass
            try:
                self.audio.play_error()
            except Exception:
                pass
            return
        tests = []
        try:
            tests = list((self._builder_exercise or {}).get("tests") or [])
        except Exception:
            tests = []
        if tests:
            ok, msg = self._run_exercise_tests(user_code, tests)
            if ok:
                self._builder_passed_via_tests = True
                self.lbl_feedback.configure(text=f"Tests: {msg}", text_color="#39FF14")
                self._on_code_builder_success()
                return
            self.code_textbox.configure(border_color="#FF3355")
            try:
                info = classify_constructor_error(
                    user_code=user_code, target_code=target_code, test_message=msg,
                )
                self._last_error_info = info
                fb, color = format_feedback(info)
                self.lbl_feedback.configure(text=(fb + f"  ·  {msg}")[:180], text_color=color)
                concept = (getattr(self, "_builder_exercise", None) or {}).get("concept", "")
                if hasattr(self.player, "record_error_class"):
                    self.player.record_error_class(concept, info.get("category", "semantic"))
                if concept:
                    self.player.record_concept_fail(concept, errors=1)
            except Exception:
                self.lbl_feedback.configure(text=msg, text_color="#FF3355")
            try:
                self._apply_line_diff(user_code, target_code)
            except Exception:
                pass
            try:
                self.audio.play_error()
            except Exception:
                pass
            return
        if self._codes_equivalent(user_code, target_code):
            self._builder_passed_via_tests = False
            self._on_code_builder_success()
            return
        self.code_textbox.configure(border_color="#FF3355")
        try:
            info = classify_constructor_error(user_code=user_code, target_code=target_code)
            self._last_error_info = info
            fb, color = format_feedback(info)
            summary = self._apply_line_diff(user_code, target_code)
            self.lbl_feedback.configure(text=f"{fb}  |  {summary}"[:200], text_color=color)
            concept = (getattr(self, "_builder_exercise", None) or {}).get("concept", "")
            if hasattr(self.player, "record_error_class"):
                self.player.record_error_class(concept, info.get("category", "semantic"))
            if concept:
                self.player.record_concept_fail(concept, errors=1)
        except Exception:
            summary = self._apply_line_diff(user_code, target_code)
            self.lbl_feedback.configure(text=f"No coincide  |  {summary}", text_color="#FF3355")
        try:
            self.audio.play_error()
        except Exception:
            pass

    def _on_code_builder_success(self):
        concept = (getattr(self, "_builder_exercise", None) or {}).get("concept", "")
        base = 25
        if getattr(self, "_builder_used_solution", False):
            base = 5
        elif getattr(self, "_builder_used_reveal", False):
            base = max(8, base - 5 * getattr(self, "_builder_revealed", 0))
        elif getattr(self, "_builder_used_scaffold", False):
            base = 15
        if getattr(self, "_builder_passed_via_tests", False):
            base += 5
        try:
            self.player.add_xp(base)
            self.player.record_challenge_completion(0, 0, len(self.current_challenge.text), concept, perfect=True)
        except Exception:
            pass
        try:
            if hasattr(self.player, "bump_contract"):
                just = self.player.bump_contract("constructor_ok", 1)
                if just and hasattr(self, "_toast_contract"):
                    self._toast_contract("◆ Contrato Constructor", "#FFB020")
            if hasattr(self, "_refresh_contracts_label"):
                self._refresh_contracts_label()
        except Exception:
            pass
        exp = self.content.get_explanation(concept, self.current_challenge)
        bonus_note = ""
        if getattr(self, "_builder_used_solution", False):
            bonus_note = " (viste la solucion)"
        elif getattr(self, "_builder_used_reveal", False):
            bonus_note = " (XP reducido por revelaciones)"
        elif getattr(self, "_builder_used_scaffold", False):
            bonus_note = " (usaste scaffold)"
        via = " · tests OK" if getattr(self, "_builder_passed_via_tests", False) else ""
        self.lbl_feedback.configure(
            text=f"Codigo correcto{via}! +{base} XP{bonus_note}",
            text_color="#39FF14",
        )
        self._builder_passed_via_tests = False
        if exp:
            self.lbl_hint.configure(text=f"📖 {exp}")
            self.lbl_hint.pack(pady=(0, 8))
        self.lbl_level.configure(text=f"LVL {self.player.level}")
        need = max(1, self.player.xp_for_next_level)
        self.progress.set(min(1.0, self.player.xp / need))
        self.after(1800, self._new_code_builder_exercise)

    def _ai_builder_hint(self):
        if self.mode != "CODE_BUILDER" or not getattr(self, "_builder_exercise", None):
            return
        if not getattr(self, "use_ai", False) or not getattr(self, "tutor", None):
            self.lbl_feedback.configure(text="Activa IA local (Ollama) para pistas del tutor", text_color="#FFB020")
            return
        try:
            self.lbl_feedback.configure(text="Consultando tutor local…", text_color="#6B7C93")
            self.update_idletasks()
            partial = self.code_textbox.get("1.0", "end-1c")
            hint = self.tutor.guided_hint(
                description=self._builder_exercise.get("description", ""),
                concept=self._builder_exercise.get("concept", ""),
                partial_code=partial,
            )
            if hint:
                self.lbl_hint.configure(text=f"🤖 {hint}")
                self.lbl_hint.pack(pady=(0, 8))
                self.lbl_feedback.configure(text="Pista del tutor lista", text_color="#00E5FF")
            else:
                self.lbl_feedback.configure(text="El tutor no respondio; prueba Scaffold o Revelar linea", text_color="#FFB020")
        except Exception as e:
            self.lbl_feedback.configure(text=f"Tutor no disponible: {e}", text_color="#FF3355")
