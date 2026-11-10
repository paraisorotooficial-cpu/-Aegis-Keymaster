"""Content Generator Module - Python challenges with blanks and explanations"""
import random
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class Challenge:
    text: str
    difficulty: int
    category: str
    concept: str
    hint: str = ""
    challenge_type: str = "full"
    prompt: str = ""
    explanation: str = ""


class ContentGenerator:
    def __init__(self):
        self.learning_paths = self._init_learning_paths()
        self.code_builder_exercises = self._init_code_builder_exercises()
        self.use_ai = False
        self._tutor = None
        self._ai_ratio = 0.55
        self.adaptive = True
        self._weak_concepts = []
        self._due_concepts = []
        self._player_level = 1
        self.daily_challenges = []
        self._generate_daily_challenges()

    def set_ai(self, enabled: bool, tutor=None):
        self.use_ai = bool(enabled)
        if tutor is not None:
            self._tutor = tutor

    def set_ai_ratio(self, ratio: float):
        try:
            self._ai_ratio = max(0.0, min(1.0, float(ratio)))
        except (TypeError, ValueError):
            self._ai_ratio = 0.55

    def set_adaptive(self, enabled: bool):
        self.adaptive = bool(enabled)

    def set_learner_context(self, weak_concepts=None, level: int = 1, due_concepts=None):
        self._weak_concepts = list(weak_concepts or [])
        self._due_concepts = list(due_concepts or [])
        self._player_level = max(1, int(level or 1))

    def _tutor_ok(self):
        if not self.use_ai:
            return False
        if self._tutor is None:
            try:
                from ollama_tutor import get_tutor
                self._tutor = get_tutor()
            except Exception:
                return False
        try:
            return self._tutor.is_available()
        except Exception:
            return False

    def _init_learning_paths(self) -> Dict[str, List[Challenge]]:
        return {
            "basics": [
                Challenge("x = 42", 1, "basics", "variables", "Asignar entero"),
                Challenge("name = 'Python'", 1, "basics", "variables", "Asignar string"),
                Challenge("is_active = True", 1, "basics", "variables", "Booleano"),
                Challenge("data = None", 1, "basics", "variables", "None"),
                Challenge("print('Hello World')", 1, "basics", "output", "Print"),
                Challenge("print(f'Value: {x}')", 2, "basics", "output", "F-string"),
                Challenge("result = 10 + 5", 2, "basics", "operations", "Suma"),
                Challenge("total = sum([1, 2, 3])", 2, "basics", "operations", "sum"),
                Challenge("length = len('hello')", 2, "basics", "operations", "len"),
                Challenge("42", 1, "basics", "variables", "Entero", "blank", "x = ____", "Asignar crea la variable; el tipo se infiere."),
                Challenge("True", 1, "basics", "variables", "Booleano", "blank", "is_active = ____", "True/False van con mayuscula."),
                Challenge("None", 1, "basics", "variables", "Nulo", "blank", "data = ____", "None es el valor nulo; se compara con is."),
                Challenge("len", 2, "basics", "operations", "Longitud", "blank", "length = ____('hello')", "len() sirve para str, list, dict, etc."),
                Challenge("sum", 2, "basics", "operations", "Suma", "blank", "total = ____([1, 2, 3])", "sum() suma elementos de un iterable."),
                Challenge("f", 2, "basics", "output", "f-string", "blank", "print(____'Value: {x}')", "Las f-strings interpolan con llaves."),
            ],
            "data_structures": [
                Challenge("numbers = [1, 2, 3]", 2, "data_structures", "lists", "Lista"),
                Challenge("nums.append(4)", 2, "data_structures", "lists", "append"),
                Challenge("user = {'name': 'Ana'}", 3, "data_structures", "dicts", "Dict"),
                Challenge("append", 2, "data_structures", "lists", "Agregar", "blank", "nums.____(4)", "append modifica in-place y devuelve None."),
                Challenge("get", 3, "data_structures", "dicts", "Acceso seguro", "blank", "name = user.____('name')", "dict.get evita KeyError."),
            ],
            "control_flow": [
                Challenge("if x > 0:\n    print('positive')", 3, "control_flow", "conditionals", "if"),
                Challenge("for i in range(5):\n    print(i)", 3, "control_flow", "loops", "for range"),
                Challenge("range", 3, "control_flow", "loops", "Rango", "blank", "for i in ____(5):\n    print(i)", "range(n) produce 0..n-1."),
            ],
            "functions": [
                Challenge("def greet(name):\n    return f'Hi {name}'", 3, "functions", "basic", "def return"),
                Challenge("return", 3, "functions", "basic", "Devolver", "blank", "def add(a, b):\n    ____ a + b", "return sale de la funcion con un valor."),
            ],
            "oop": [
                Challenge("class Dog:\n    def __init__(self, name):\n        self.name = name", 5, "oop", "classes", "Clase basica"),
            ],
            "modules": [
                Challenge("import math\nprint(math.sqrt(16))", 4, "modules", "import", "import"),
            ],
            "file_io": [
                Challenge("with open('f.txt') as f:\n    data = f.read()", 5, "file_io", "file_io", "with open"),
            ],
            "exceptions": [
                Challenge("try:\n    x = 1 / 0\nexcept ZeroDivisionError:\n    x = 0", 5, "exceptions", "exceptions", "try except"),
            ],
            "advanced": [
                Challenge("[x*x for x in range(5)]", 6, "advanced", "comprehensions", "list comp"),
            ],
            "stdlib": [
                Challenge("from collections import Counter", 5, "stdlib", "collections", "Counter"),
            ],
            "best_practices": [
                Challenge("if not items:\n    return", 4, "best_practices", "style", "early return"),
            ],
        }

    def get_challenge(self, difficulty: int, path: str = None, prefer_blank: bool = False) -> Challenge:
        if self._tutor_ok() and random.random() < self._ai_ratio:
            try:
                focus = None
                if self.adaptive:
                    focus = list(dict.fromkeys((self._due_concepts or []) + (self._weak_concepts or [])))[:6]
                data = self._tutor.generate_challenge(
                    path=path or "basics",
                    difficulty=difficulty,
                    prefer_blank=prefer_blank,
                    focus_concepts=focus,
                )
                if data:
                    return Challenge(
                        text=data["text"],
                        difficulty=data.get("difficulty", difficulty),
                        category=data.get("category", path or "ai"),
                        concept=data.get("concept", "ai"),
                        hint=data.get("hint", ""),
                        challenge_type=data.get("challenge_type", "full"),
                        prompt=data.get("prompt", ""),
                        explanation=data.get("explanation", ""),
                    )
            except Exception:
                pass

        def _pick(candidates):
            if not candidates:
                return None
            pool = list(candidates)
            if prefer_blank:
                blanks = [c for c in pool if getattr(c, "challenge_type", "full") == "blank"]
                if blanks and random.random() < 0.45:
                    pool = blanks
            if self.adaptive and (self._weak_concepts or self._due_concepts):
                weak = set(self._weak_concepts or [])
                due = set(self._due_concepts or [])
                weighted = []
                for c in pool:
                    w = 1
                    if c.concept in due:
                        w += 5
                    if c.concept in weak:
                        w += 2
                    weighted.extend([c] * w)
                return random.choice(weighted)
            return random.choice(pool)
        if path and path in self.learning_paths:
            candidates = [ch for ch in self.learning_paths[path] if abs(ch.difficulty - difficulty) <= 2]
            picked = _pick(candidates)
            if picked:
                return picked
        all_ch = []
        for challenges in self.learning_paths.values():
            all_ch.extend([ch for ch in challenges if abs(ch.difficulty - difficulty) <= 2])
        picked = _pick(all_ch)
        if picked:
            return picked
        all_ch = [ch for challenges in self.learning_paths.values() for ch in challenges]
        return random.choice(all_ch)

    def get_path_progress(self, path: str, completed_concepts: set) -> Tuple[int, int]:
        if path not in self.learning_paths:
            return 0, 0
        concepts = set(ch.concept for ch in self.learning_paths[path])
        return len(concepts & completed_concepts), len(concepts)

    def get_path_concepts(self, path: str) -> list:
        if path not in self.learning_paths:
            return []
        seen = []
        for ch in self.learning_paths[path]:
            c = getattr(ch, "concept", "") or ""
            if c and c not in seen:
                seen.append(c)
        return seen

    def get_path_checklist(self, path: str, concept_stats: dict = None, completed_concepts=None) -> list:
        concept_stats = concept_stats or {}
        completed = set(completed_concepts or [])
        rows = []
        for concept in self.get_path_concepts(path):
            st = concept_stats.get(concept, {}) or {}
            attempts = int(st.get("attempts", 0) or 0)
            successes = int(st.get("successes", 0) or 0)
            fails = int(st.get("fails", 0) or 0)
            nr = st.get("next_review")
            due = False
            if nr:
                try:
                    from datetime import datetime
                    d = datetime.strptime(str(nr)[:10], "%Y-%m-%d").date()
                    due = d <= datetime.now().date()
                except Exception:
                    due = False
            if successes >= 2 and fails / max(1, attempts) < 0.35:
                status = "mastered"
            elif concept in completed and successes >= 1:
                status = "mastered"
            elif due:
                status = "due"
            elif attempts > 0:
                status = "learning"
            else:
                status = "todo"
            rows.append({
                "concept": concept,
                "status": status,
                "attempts": attempts,
                "successes": successes,
                "fails": fails,
            })
        return rows

    def _generate_daily_challenges(self):
        self.daily_challenges = [self.get_challenge(3), self.get_challenge(6), self.get_challenge(9)]

    def get_daily_challenges(self) -> List[Challenge]:
        return self.daily_challenges

    def get_available_paths(self) -> List[str]:
        return list(self.learning_paths.keys())

    def get_path_name(self, path: str) -> str:
        names = {"basics": "Fundamentos", "data_structures": "Estructuras de Datos", "control_flow": "Control de Flujo", "functions": "Funciones", "oop": "POO", "modules": "Modulos", "file_io": "Archivos I/O", "exceptions": "Excepciones", "advanced": "Avanzado", "stdlib": "Stdlib", "best_practices": "Buenas Practicas"}
        return names.get(path, path.title())

    def get_recommended_path_order(self) -> List[str]:
        return ["basics", "data_structures", "control_flow", "functions", "modules", "file_io", "exceptions", "oop", "stdlib", "best_practices", "advanced"]

    def get_explanation(self, concept: str, challenge: Challenge = None) -> str:
        if challenge is not None and getattr(challenge, "explanation", ""):
            return challenge.explanation
        tips = {"variables": "Las variables se crean al asignar; no declaras el tipo.", "operations": "Prefiere built-ins (len, sum, round) cuando baste.", "output": "print acepta varios args; f-strings son la forma moderna.", "lists": "Las listas son mutables; append modifica in-place.", "dicts": "Usa .get() para acceso seguro sin KeyError.", "loops": "for itera iterables; range genera enteros (fin exclusivo).", "conditionals": "Tras if/else va ':' y el bloque indentado.", "basic": "def nombre(params): y return para devolver valor.", "lambda": "lambda args: expr — una sola expresion.", "classes": "class + __init__(self, ...) para estado.", "exceptions": "try/except atrapa errores.", "file_io": "with open cierra el archivo aunque haya errores."}
        return tips.get(concept, "Practica este patron hasta automatizarlo.")

    def get_challenge_display_text(self, challenge: Challenge) -> str:
        if getattr(challenge, "challenge_type", "full") == "blank" and challenge.prompt:
            return challenge.prompt
        return challenge.text

    def _init_code_builder_exercises(self) -> Dict[str, List[Dict]]:
        try:
            from builder_content import BUILDER_EXERCISES
            return BUILDER_EXERCISES
        except ImportError:
            return {"basic_functions": [{"title": "Suma", "difficulty": 2, "code": "def sumar(a, b):\n    return a + b", "scaffold": "def sumar(a, b):\n    pass", "description": "Suma dos numeros", "goals": ["return a + b"], "concept": "functions"}]}

    def get_code_builder_exercise(self, difficulty: int = None, category: str = None):
        if self._tutor_ok() and random.random() < self._ai_ratio:
            try:
                focus = None
                if self.adaptive:
                    focus = list(dict.fromkeys((self._due_concepts or []) + (self._weak_concepts or [])))[:6]
                data = self._tutor.generate_builder_exercise(
                    category=category or "basic_functions",
                    difficulty=difficulty or 3,
                    focus_concepts=focus,
                )
                if data:
                    return data
            except Exception:
                pass
        if category and category in self.code_builder_exercises:
            exercises = self.code_builder_exercises[category]
            if difficulty:
                filtered = [ex for ex in exercises if abs(ex['difficulty'] - difficulty) <= 2]
                if filtered:
                    return random.choice(filtered)
            return random.choice(exercises)
        all_ex = []
        for exercises in self.code_builder_exercises.values():
            all_ex.extend(exercises)
        return random.choice(all_ex) if all_ex else None

    def get_code_builder_categories(self) -> List[str]:
        return list(self.code_builder_exercises.keys())

    def get_code_builder_structure_hint(self, exercise: dict) -> str:
        code = exercise.get("code", "")
        lines = code.split("\n")
        goals = exercise.get("goals") or []
        parts = [f"{len(lines)} lineas esperadas"]
        if goals:
            parts.append("Objetivos: " + "; ".join(goals[:4]))
        keys = []
        for kw in ("def ", "class ", "for ", "while ", "if ", "return ", "with ", "try:", "lambda "):
            if kw in code:
                keys.append(kw.strip().rstrip(":"))
        if keys:
            parts.append("Palabras clave: " + ", ".join(keys))
        return " | ".join(parts)

    def get_category_name(self, category: str) -> str:
        names = {"basic_functions": "Funciones Basicas", "loops_practice": "Practica de Bucles", "list_operations": "Operaciones con Listas", "dict_operations": "Operaciones con Dicts", "classes_basic": "Clases Basicas", "error_handling": "Manejo de Errores", "file_operations": "Operaciones con Archivos", "advanced_concepts": "Conceptos Avanzados"}
        return names.get(category, category.replace('_', ' ').title())
