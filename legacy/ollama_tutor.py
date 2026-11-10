"""
OllamaTutor — LLM local via Ollama for dynamic challenges and guided feedback.

Requires Ollama running (https://ollama.com) e.g.:
  ollama pull llama3.2
  ollama serve

The app works fully offline without Ollama; AI features degrade gracefully.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional


DEFAULT_HOST = "http://127.0.0.1:11434"
PREFERRED_MODELS = (
    "llama3.2",
    "llama3.2:3b",
    "llama3.2:1b",
    "qwen2.5-coder:3b",
    "qwen2.5-coder:1.5b",
    "phi3:mini",
    "gemma2:2b",
    "mistral",
    "codellama:7b",
)


class OllamaTutor:
    """Thin client around Ollama HTTP API (no extra pip deps)."""

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        model: Optional[str] = None,
        timeout: float = 28.0,
    ):
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._available: Optional[bool] = None
        self._models: List[str] = []

    def refresh(self) -> bool:
        try:
            data = self._get("/api/tags")
            names = [m.get("name", "") for m in data.get("models", [])]
            self._models = [n for n in names if n]
            self._available = bool(self._models)
            if self._available and not self.model:
                self.model = self._pick_model()
            return self._available
        except Exception:
            self._available = False
            self._models = []
            return False

    def is_available(self) -> bool:
        if self._available is None:
            return self.refresh()
        return bool(self._available)

    def list_models(self) -> List[str]:
        if self._available is None:
            self.refresh()
        return list(self._models)

    def _pick_model(self) -> str:
        lower = {m.lower(): m for m in self._models}
        for pref in PREFERRED_MODELS:
            if pref in lower:
                return lower[pref]
            for name, orig in lower.items():
                if name.startswith(pref) or pref in name:
                    return orig
        return self._models[0]

    def status_text(self) -> str:
        if not self.is_available():
            return "Ollama offline"
        return f"Ollama · {self.model or '?'}"

    def set_model(self, name: str) -> bool:
        """Select an installed model by name (exact or prefix)."""
        if not name:
            return False
        if self._available is None:
            self.refresh()
        models = self.list_models()
        if not models:
            return False
        lower = {m.lower(): m for m in models}
        key = name.lower().strip()
        if key in lower:
            self.model = lower[key]
            return True
        for mname, orig in lower.items():
            if mname.startswith(key) or key in mname:
                self.model = orig
                return True
        return False

    def _get(self, path: str) -> dict:
        req = urllib.request.Request(self.host + path, method="GET")
        with urllib.request.urlopen(req, timeout=min(5.0, self.timeout)) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _generate(self, prompt: str, system: str = "", json_mode: bool = True) -> str:
        if not self.is_available():
            raise RuntimeError("Ollama no disponible")
        body: Dict[str, Any] = {
            "model": self.model or self._pick_model(),
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.4,
                "num_predict": 512,
            },
        }
        if system:
            body["system"] = system
        if json_mode:
            body["format"] = "json"
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            self.host + "/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        return (payload.get("response") or "").strip()

    def _parse_json(self, text: str) -> Optional[dict]:
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            m = re.search(r"\{[\s\S]*\}", text)
            if m:
                try:
                    return json.loads(m.group(0))
                except json.JSONDecodeError:
                    return None
        return None

    SYSTEM_CHALLENGE = (
        "Eres un tutor de Python para principiantes e intermedios. "
        "Responde SOLO JSON valido, sin markdown. "
        "El codigo debe ser Python 3 correcto, corto (1-4 lineas), listo para teclear."
    )

    def generate_challenge(
        self,
        path: str = "basics",
        difficulty: int = 2,
        prefer_blank: bool = False,
        focus_concepts: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        kind = (
            "blank (solo la palabra/expresion que falta en answer, prompt con ____)"
            if prefer_blank
            else "full (codigo completo en answer)"
        )
        focus = ""
        if focus_concepts:
            focus = (
                "El alumno necesita reforzar estos conceptos: "
                + ", ".join(focus_concepts[:5])
                + ". Prioriza practicar uno de ellos.\n"
            )
        prompt = f"""Genera UN desafio de tecleo/practica de Python.
Ruta: {path}
Dificultad 1-10: {difficulty}
Tipo: {kind}
{focus}
JSON exacto:
{{
  "answer": "codigo o fragmento correcto a teclear",
  "prompt": "si blank: linea con ____ ; si full: string vacio",
  "concept": "concepto corto en ingles snake (ej variables, loops)",
  "hint": "pista breve en espanol",
  "explanation": "1-2 frases pedagogicas en espanol",
  "title": "titulo corto"
}}
Reglas: answer debe ser valido; sin imports raros; sin comentarios; ASCII preferido."""
        try:
            raw = self._generate(prompt, system=self.SYSTEM_CHALLENGE, json_mode=True)
            data = self._parse_json(raw)
            if not data or not data.get("answer"):
                return None
            answer = str(data["answer"]).strip()
            if len(answer) > 200 or answer.count("\n") > 5:
                return None
            is_blank = prefer_blank or (data.get("prompt") and "____" in str(data.get("prompt")))
            return {
                "text": answer,
                "difficulty": max(1, min(10, int(data.get("difficulty", difficulty) or difficulty))),
                "category": path,
                "concept": str(data.get("concept") or path),
                "hint": str(data.get("hint") or "Sigue el patron"),
                "challenge_type": "blank" if is_blank else "full",
                "prompt": str(data.get("prompt") or ""),
                "explanation": str(data.get("explanation") or ""),
                "title": str(data.get("title") or ""),
                "source": "ollama",
            }
        except Exception:
            return None

    SYSTEM_BUILDER = (
        "Eres un profesor de Python. Generas ejercicios de escribir funciones/bloques. "
        "Responde SOLO JSON valido. El codigo debe ser sintacticamente correcto."
    )

    def generate_builder_exercise(
        self,
        category: str = "basic_functions",
        difficulty: int = 3,
        focus_concepts: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        focus = ""
        if focus_concepts:
            focus = "Refuerza: " + ", ".join(focus_concepts[:4]) + ".\n"
        prompt = f"""Genera UN ejercicio de code-builder (escribir un bloque completo).
Categoria: {category}
Dificultad 1-10: {difficulty}
{focus}
JSON exacto:
{{
  "title": "titulo corto",
  "difficulty": {difficulty},
  "code": "codigo completo multilinea con \\n reales en el JSON",
  "scaffold": "misma firma con pass o TODO",
  "description": "que debe hacer, en espanol",
  "goals": ["objetivo1", "objetivo2"],
  "concept": "concepto corto",
  "hint": "pista en espanol"
}}
Reglas: 3-12 lineas; sin imports externos; Python 3 puro; indentacion 4 espacios."""
        try:
            raw = self._generate(prompt, system=self.SYSTEM_BUILDER, json_mode=True)
            data = self._parse_json(raw)
            if not data or not data.get("code"):
                return None
            code = str(data["code"]).replace("\\n", "\n")
            if "\n" not in code and len(code) < 10:
                return None
            try:
                import ast
                ast.parse(code)
            except SyntaxError:
                return None
            scaffold = str(data.get("scaffold") or "").replace("\\n", "\n")
            goals = data.get("goals") or []
            if isinstance(goals, str):
                goals = [goals]
            return {
                "title": str(data.get("title") or "Ejercicio IA"),
                "difficulty": max(1, min(10, int(data.get("difficulty", difficulty) or difficulty))),
                "code": code,
                "scaffold": scaffold,
                "description": str(data.get("description") or "Completa el codigo"),
                "goals": list(goals)[:5],
                "concept": str(data.get("concept") or category),
                "hint": str(data.get("hint") or ""),
                "source": "ollama",
            }
        except Exception:
            return None

    SYSTEM_TUTOR = (
        "Eres un tutor paciente de Python. Responde en espanol, breve (2-4 frases), "
        "concreto y pedagogico. No des el codigo completo a menos que sea inevitable; "
        "senala el error y la idea correcta."
    )

    def explain_mismatch(
        self,
        user_code: str,
        target_code: str,
        concept: str = "",
        description: str = "",
    ) -> Optional[str]:
        prompt = f"""El alumno escribio un codigo que no coincide con la solucion esperada.

Concepto: {concept or 'python'}
Enunciado: {description or 'N/A'}

Codigo del alumno:
```
{user_code[:800]}
```

Solucion esperada (NO la copies entera al alumno):
```
{target_code[:800]}
```

Da feedback guiado: que esta mal o incompleto, y como pensarlo. Max 4 frases."""
        try:
            text = self._generate(prompt, system=self.SYSTEM_TUTOR, json_mode=False)
            text = (text or "").strip()
            if len(text) > 600:
                text = text[:600] + "…"
            return text or None
        except Exception:
            return None

    def guided_hint(
        self,
        description: str,
        concept: str = "",
        partial_code: str = "",
    ) -> Optional[str]:
        prompt = f"""Pista corta para un alumno que esta atascado.

Concepto: {concept or 'python'}
Enunciado: {description}
Codigo parcial del alumno:
```
{(partial_code or '(vacio)')[:400]}
```

Una pista (no la solucion completa), 1-3 frases en espanol."""
        try:
            text = self._generate(prompt, system=self.SYSTEM_TUTOR, json_mode=False)
            text = (text or "").strip()
            if len(text) > 400:
                text = text[:400] + "…"
            return text or None
        except Exception:
            return None


_tutor: Optional[OllamaTutor] = None


def get_tutor(force_refresh: bool = False) -> OllamaTutor:
    global _tutor
    if _tutor is None:
        _tutor = OllamaTutor()
    if force_refresh or _tutor._available is None:
        _tutor.refresh()
    return _tutor
