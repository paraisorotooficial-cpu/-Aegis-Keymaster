"""
Profile Manager Module
Handles player progression, statistics, and data persistence
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Set
from achievements import AchievementManager
try:
    from daily_contracts import DailyContractsMixin
except Exception:
    DailyContractsMixin = object


class PlayerProfile(DailyContractsMixin):
    """Manages player profile, progression, and statistics"""
    
    def __init__(self):
        self.filename = "keymaster_profile.json"
        self.xp = 0
        self.level = 1
        self.total_challenges_completed = 0
        self.perfect_challenges = 0
        self.best_survival_score = 0
        self.fastest_wpm = 0
        self.total_keystrokes = 0
        self.total_errors = 0
        self.total_time_played = 0
        self.completed_concepts: Set[str] = set()
        self.concept_stats: Dict[str, Dict[str, int]] = {}
        self.current_learning_path = "basics"
        self.mastered_paths: Set[str] = set()
        self.daily_completed = []
        self.daily_streak = 0
        self.last_daily_date = ""
        self.contracts_date = ""
        self.contracts = []
        self.contracts_claimed = False
        self.onboarding_done = False
        self.onboarding_level_key = ""
        self.error_breakdown = {}
        self.powerups = {"hint": 3, "skip": 2, "slow_time": 1}
        self.highest_combo = 0
        self.achievement_manager = AchievementManager()
        self.load_profile()
        try:
            self.ensure_daily_contracts()
        except Exception:
            pass
    
    @property
    def rank(self) -> str:
        ranks = {1: "🐣 Novato", 5: "📜 Scripter", 10: "💻 Coder", 15: "🔧 Developer", 20: "🎯 Senior Dev", 30: "🚀 Tech Lead", 40: "🧙 Architect", 50: "👑 Guru", 75: "🌟 Legend", 100: "🤖 AI Singularity"}
        for lvl in sorted(ranks.keys(), reverse=True):
            if self.level >= lvl:
                return ranks[lvl]
        return "Unknown"
    
    @property
    def xp_for_next_level(self) -> int:
        return self.level * 100
    
    @property
    def accuracy(self) -> float:
        if self.total_keystrokes == 0:
            return 100.0
        return ((self.total_keystrokes - self.total_errors) / self.total_keystrokes) * 100
    
    def add_xp(self, amount: int) -> bool:
        self.xp += amount
        leveled_up = False
        while self.xp >= self.xp_for_next_level:
            self.xp -= self.xp_for_next_level
            self.level += 1
            leveled_up = True
            self.earn_powerup("hint", 1)
            if self.level % 5 == 0:
                self.earn_powerup("skip", 1)
            if self.level % 10 == 0:
                self.earn_powerup("slow_time", 1)
        if leveled_up or amount > 0:
            self.save_profile()
        return leveled_up
    
    def record_challenge_completion(self, wpm: int, errors: int, keystrokes: int, concept: str = "", perfect: bool = False):
        self.total_challenges_completed += 1
        self.achievement_manager.stats["total_challenges"] += 1
        if perfect:
            self.perfect_challenges += 1
            self.achievement_manager.stats["perfect_challenges"] += 1
        if wpm > self.fastest_wpm:
            self.fastest_wpm = wpm
            self.achievement_manager.stats["fastest_wpm"] = wpm
        self.total_keystrokes += keystrokes
        self.total_errors += errors
        self.achievement_manager.stats["total_keystrokes"] += keystrokes
        self.achievement_manager.stats["errors_made"] += errors
        if concept:
            self.completed_concepts.add(concept)
            self.achievement_manager.stats["python_concepts_mastered"].add(concept)
            self._touch_concept(concept, errors=errors, success=True, perfect=perfect)
        self.save_profile()
    
    def update_survival_score(self, score: int, combo: int) -> bool:
        is_high_score = score > self.best_survival_score
        if is_high_score:
            self.best_survival_score = score
            self.achievement_manager.stats["best_survival_score"] = score
        if combo > self.highest_combo:
            self.highest_combo = combo
            self.achievement_manager.stats["highest_combo"] = combo
        self.save_profile()
        return is_high_score
    
    def update_combo(self, combo: int):
        if combo > self.highest_combo:
            self.highest_combo = combo
            self.achievement_manager.stats["highest_combo"] = combo
            self.save_profile()
    
    def complete_daily_challenge(self, challenge_id: int):
        today = datetime.now().strftime("%Y-%m-%d")
        if self.last_daily_date != today:
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            if self.last_daily_date == yesterday:
                self.daily_streak += 1
            else:
                self.daily_streak = 1
            self.daily_completed = []
            self.last_daily_date = today
        if challenge_id not in self.daily_completed:
            self.daily_completed.append(challenge_id)
        self.save_profile()
    
    def use_powerup(self, powerup_type: str) -> bool:
        if self.powerups.get(powerup_type, 0) > 0:
            self.powerups[powerup_type] -= 1
            self.save_profile()
            return True
        return False
    
    def earn_powerup(self, powerup_type: str, amount: int = 1):
        if powerup_type in self.powerups:
            self.powerups[powerup_type] += amount
            self.save_profile()
    
    def check_achievements(self) -> list:
        return self.achievement_manager.check_achievements()

    SRS_INTERVALS = (1, 3, 7, 14, 30, 60)

    def _schedule_review(self, st: dict, success: bool, perfect: bool = False, errors: int = 0):
        try:
            from fsrs import review as fsrs_review, ensure_card
            ensure_card(st)
            fsrs_review(st, success=success, perfect=perfect, errors=errors)
            return
        except Exception:
            pass
        today = datetime.now().date()
        if success:
            prev = int(st.get("srs_step", 0) or 0)
            idx = min(len(self.SRS_INTERVALS) - 1, prev + (2 if perfect else 1))
            days = self.SRS_INTERVALS[idx]
            st["srs_step"] = idx
            st["interval_days"] = days
            st["next_review"] = (today + timedelta(days=days)).isoformat()
            st["consecutive_correct"] = int(st.get("consecutive_correct", 0) or 0) + 1
        else:
            st["srs_step"] = 0
            st["interval_days"] = 1
            st["next_review"] = (today + timedelta(days=1)).isoformat()
            st["consecutive_correct"] = 0
        st["last_reviewed"] = today.isoformat()

    def _touch_concept(self, concept: str, errors: int = 0, success: bool = False, perfect: bool = False):
        if not concept:
            return
        st = self.concept_stats.setdefault(concept, {
            "attempts": 0, "errors": 0, "successes": 0, "fails": 0,
            "srs_step": 0, "interval_days": 0, "next_review": None,
            "consecutive_correct": 0, "last_reviewed": None,
            "fsrs_difficulty": None, "fsrs_stability": None,
            "fsrs_reps": 0, "fsrs_lapses": 0,
        })
        st["attempts"] = st.get("attempts", 0) + 1
        st["errors"] = st.get("errors", 0) + max(0, int(errors or 0))
        if success:
            st["successes"] = st.get("successes", 0) + 1
        else:
            st["fails"] = st.get("fails", 0) + 1
        try:
            self._schedule_review(st, success=success, perfect=perfect, errors=errors)
        except Exception:
            pass

    def record_concept_fail(self, concept: str, errors: int = 1):
        if concept:
            self._touch_concept(concept, errors=errors, success=False)
            self.save_profile()

    def record_error_class(self, concept: str, category: str):
        category = (category or "other").strip().lower() or "other"
        if not hasattr(self, "error_breakdown") or self.error_breakdown is None:
            self.error_breakdown = {}
        self.error_breakdown[category] = int(self.error_breakdown.get(category, 0) or 0) + 1
        if concept:
            st = self.concept_stats.setdefault(concept, {})
            eb = st.setdefault("error_classes", {})
            eb[category] = int(eb.get(category, 0) or 0) + 1
        try:
            self.save_profile()
        except Exception:
            pass

    def get_error_breakdown(self) -> dict:
        return dict(getattr(self, "error_breakdown", {}) or {})

    def get_due_concepts(self, limit: int = 8) -> list:
        today = datetime.now().date()
        due = []
        try:
            from fsrs import is_due
        except Exception:
            is_due = None
        for concept, st in self.concept_stats.items():
            if is_due is not None:
                try:
                    due_flag, r = is_due(st, today)
                    if due_flag:
                        due.append((r, concept))
                    continue
                except Exception:
                    pass
            nr = st.get("next_review")
            if not nr:
                if st.get("fails", 0) > 0 or (st.get("successes", 0) == 0 and st.get("attempts", 0) > 0):
                    due.append((0.0, concept))
                continue
            try:
                d = datetime.strptime(str(nr)[:10], "%Y-%m-%d").date()
            except Exception:
                continue
            if d <= today:
                due.append((0.0, concept))
        due.sort()
        return [c for _, c in due[:limit]]

    def get_review_schedule(self, limit: int = 12) -> list:
        today = datetime.now().date()
        items = []
        try:
            from fsrs import schedule_summary
        except Exception:
            schedule_summary = None
        for concept, st in self.concept_stats.items():
            if schedule_summary is not None:
                try:
                    row = schedule_summary(st, today)
                    row["concept"] = concept
                    items.append(row)
                    continue
                except Exception:
                    pass
            nr = st.get("next_review")
            interval = st.get("interval_days", 0)
            if not nr:
                status = "pendiente"
                days_left = 0
            else:
                try:
                    d = datetime.strptime(str(nr)[:10], "%Y-%m-%d").date()
                    days_left = (d - today).days
                    status = f"vencido {-days_left}d" if days_left < 0 else ("hoy" if days_left == 0 else f"en {days_left}d")
                except Exception:
                    status = "?"
                    days_left = 999
            items.append({"concept": concept, "status": status, "days_left": days_left, "interval": interval,
                "step": st.get("srs_step", 0), "next_review": nr, "stability": st.get("fsrs_stability"),
                "difficulty": st.get("fsrs_difficulty"), "retrievability": None, "due": days_left <= 0,
                "reps": st.get("fsrs_reps", 0), "lapses": st.get("fsrs_lapses", 0)})
        items.sort(key=lambda x: (x.get("days_left", 999), x.get("concept", "")))
        return items[:limit]

    def get_weak_concepts(self, limit: int = 5) -> list:
        scored = []
        due_set = set(self.get_due_concepts(limit=20))
        for concept, st in self.concept_stats.items():
            attempts = max(1, st.get("attempts", 0))
            fails = st.get("fails", 0)
            errs = st.get("errors", 0)
            successes = st.get("successes", 0)
            score = (fails / attempts) * 2.0 + (errs / attempts) * 0.5
            if successes == 0 and attempts >= 1:
                score += 0.4
            if concept in due_set:
                score += 1.5
            if score > 0.05:
                scored.append((score, concept))
        scored.sort(reverse=True)
        return [c for _, c in scored[:limit]]

    def get_strong_concepts(self) -> set:
        strong = set()
        for concept, st in self.concept_stats.items():
            attempts = st.get("attempts", 0)
            successes = st.get("successes", 0)
            fails = st.get("fails", 0)
            if attempts >= 3 and successes >= 2 and fails / max(1, attempts) < 0.25:
                strong.add(concept)
        return strong

    def save_profile(self):
        data = {
            "xp": self.xp, "level": self.level,
            "total_challenges_completed": self.total_challenges_completed,
            "perfect_challenges": self.perfect_challenges,
            "best_survival_score": self.best_survival_score,
            "fastest_wpm": self.fastest_wpm,
            "total_keystrokes": self.total_keystrokes,
            "total_errors": self.total_errors,
            "total_time_played": self.total_time_played,
            "completed_concepts": list(self.completed_concepts),
            "concept_stats": self.concept_stats,
            "current_learning_path": self.current_learning_path,
            "mastered_paths": list(self.mastered_paths),
            "daily_completed": self.daily_completed,
            "daily_streak": self.daily_streak,
            "last_daily_date": self.last_daily_date,
            "contracts_date": getattr(self, "contracts_date", ""),
            "contracts": getattr(self, "contracts", []),
            "contracts_claimed": getattr(self, "contracts_claimed", False),
            "onboarding_done": getattr(self, "onboarding_done", False),
            "onboarding_level_key": getattr(self, "onboarding_level_key", ""),
            "error_breakdown": getattr(self, "error_breakdown", {}),
            "powerups": self.powerups,
            "highest_combo": self.highest_combo,
            "achievements": self.achievement_manager.to_dict()
        }
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_profile(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.xp = data.get("xp", 0)
                self.level = data.get("level", 1)
                self.total_challenges_completed = data.get("total_challenges_completed", 0)
                self.perfect_challenges = data.get("perfect_challenges", 0)
                self.best_survival_score = data.get("best_survival_score", 0)
                self.fastest_wpm = data.get("fastest_wpm", 0)
                self.total_keystrokes = data.get("total_keystrokes", 0)
                self.total_errors = data.get("total_errors", 0)
                self.total_time_played = data.get("total_time_played", 0)
                self.completed_concepts = set(data.get("completed_concepts", []))
                self.concept_stats = data.get("concept_stats", {}) or {}
                self.current_learning_path = data.get("current_learning_path", "basics")
                self.mastered_paths = set(data.get("mastered_paths", []))
                self.daily_completed = data.get("daily_completed", [])
                self.daily_streak = data.get("daily_streak", 0)
                self.last_daily_date = data.get("last_daily_date", "")
                self.contracts_date = data.get("contracts_date", "")
                self.contracts = data.get("contracts", []) or []
                self.contracts_claimed = bool(data.get("contracts_claimed", False))
                self.onboarding_done = bool(data.get("onboarding_done", False))
                self.onboarding_level_key = data.get("onboarding_level_key", "")
                self.error_breakdown = data.get("error_breakdown", {}) or {}
                self.powerups = data.get("powerups", {"hint": 3, "skip": 2, "slow_time": 1})
                self.highest_combo = data.get("highest_combo", 0)
                if "achievements" in data:
                    self.achievement_manager.from_dict(data["achievements"])
            except Exception as e:
                print(f"Error loading profile: {e}")
    
    def get_stats_summary(self) -> Dict:
        return {
            "level": self.level, "xp": self.xp, "rank": self.rank,
            "accuracy": round(self.accuracy, 1),
            "challenges": self.total_challenges_completed,
            "perfect": self.perfect_challenges,
            "best_wpm": self.fastest_wpm,
            "survival": self.best_survival_score,
            "streak": self.daily_streak,
            "concepts": len(self.completed_concepts),
            "weak": self.get_weak_concepts(3),
            "due": self.get_due_concepts(5),
            "due_count": len(self.get_due_concepts(50)),
            "error_breakdown": self.get_error_breakdown(),
            "contracts": self.get_contracts_progress() if hasattr(self, "get_contracts_progress") else {},
        }
