"""
Daily contracts (misiones del día) for KeyMaster.

Three missions roll each calendar day. Progress is tracked in the player profile
and advanced from gameplay events (typing success, constructor tests, FSRS due reviews).
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
import hashlib

TEMPLATES = [
    {
        "id": "blanks_perfect",
        "label": "Completa {n} huecos perfectos (sin errores)",
        "event": "blank_perfect",
        "target": 2,
        "xp": 25,
    },
    {
        "id": "constructor_tests",
        "label": "Aprueba {n} ejercicios de Constructor (tests OK)",
        "event": "constructor_ok",
        "target": 1,
        "xp": 30,
    },
    {
        "id": "review_due",
        "label": "Repasa {n} conceptos con revisión pendiente (FSRS)",
        "event": "due_review",
        "target": 1,
        "xp": 25,
    },
    {
        "id": "training_reps",
        "label": "Completa {n} retos de Entrenamiento",
        "event": "training_ok",
        "target": 5,
        "xp": 20,
    },
    {
        "id": "learning_reps",
        "label": "Completa {n} retos de Aprendizaje",
        "event": "learning_ok",
        "target": 3,
        "xp": 20,
    },
    {
        "id": "survival_wave",
        "label": "Alcanza score {n} en Supervivencia",
        "event": "survival_score",
        "target": 30,
        "xp": 30,
        "mode": "set_max",
    },
]


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _seed_pick(date_str: str, pool: list, k: int = 3) -> list:
    """Deterministic pick of k templates for the day."""
    if k >= len(pool):
        return list(pool)
    scored = []
    for i, t in enumerate(pool):
        h = hashlib.sha256(f"{date_str}:{t['id']}".encode()).hexdigest()
        scored.append((h, i, t))
    scored.sort()
    return [t for _, _, t in scored[:k]]


def build_contracts_for_day(date_str: Optional[str] = None) -> List[Dict[str, Any]]:
    date_str = date_str or _today()
    picked = _seed_pick(date_str, TEMPLATES, k=3)
    contracts = []
    for t in picked:
        n = t["target"]
        contracts.append({
            "id": t["id"],
            "event": t["event"],
            "target": n,
            "progress": 0,
            "done": False,
            "xp": t.get("xp", 20),
            "mode": t.get("mode", "add"),
            "label": t["label"].format(n=n),
        })
    return contracts


class DailyContractsMixin:
    def ensure_daily_contracts(self) -> List[Dict[str, Any]]:
        today = _today()
        if getattr(self, "contracts_date", "") != today or not getattr(self, "contracts", None):
            self.contracts_date = today
            self.contracts = build_contracts_for_day(today)
            self.contracts_claimed = False
            try:
                self.save_profile()
            except Exception:
                pass
        return self.contracts

    def get_contracts_progress(self) -> Dict[str, Any]:
        contracts = self.ensure_daily_contracts()
        done = sum(1 for c in contracts if c.get("done"))
        total = len(contracts) or 3
        return {
            "date": getattr(self, "contracts_date", _today()),
            "done": done,
            "total": total,
            "all_done": done >= total,
            "claimed": bool(getattr(self, "contracts_claimed", False)),
            "contracts": contracts,
            "bonus_xp": sum(c.get("xp", 0) for c in contracts) if done >= total else 0,
        }

    def bump_contract(self, event: str, value: int = 1) -> List[Dict[str, Any]]:
        contracts = self.ensure_daily_contracts()
        just_done = []
        for c in contracts:
            if c.get("done"):
                continue
            if c.get("event") != event:
                continue
            mode = c.get("mode", "add")
            if mode == "set_max":
                c["progress"] = max(int(c.get("progress", 0)), int(value))
            else:
                c["progress"] = int(c.get("progress", 0)) + int(value)
            if c["progress"] >= int(c.get("target", 1)):
                c["progress"] = int(c.get("target", 1))
                c["done"] = True
                just_done.append(dict(c))
        if just_done or value:
            try:
                self.save_profile()
            except Exception:
                pass
        return just_done

    def claim_contracts_bonus(self) -> int:
        info = self.get_contracts_progress()
        if not info["all_done"] or info["claimed"]:
            return 0
        bonus = sum(c.get("xp", 0) for c in info["contracts"])
        bonus += 15
        self.contracts_claimed = True
        try:
            self.add_xp(bonus)
            self.save_profile()
        except Exception:
            try:
                self.save_profile()
            except Exception:
                pass
        return bonus
