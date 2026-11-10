"""
Achievement System Module
Tracks and manages player achievements and milestones
"""
from typing import Dict, List
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Achievement:
    """Represents a single achievement"""
    id: str
    name: str
    description: str
    icon: str
    requirement: int
    unlocked: bool = False
    unlock_date: str = ""
    category: str = "general"


class AchievementManager:
    """Manages all achievements and progression tracking"""
    
    def __init__(self):
        self.achievements = self._init_achievements()
        self.stats = {
            "total_challenges": 0,
            "perfect_challenges": 0,
            "total_keystrokes": 0,
            "errors_made": 0,
            "fastest_wpm": 0,
            "total_xp_earned": 0,
            "survival_runs": 0,
            "highest_combo": 0,
            "time_played_seconds": 0,
            "python_concepts_mastered": set()
        }
    
    def _init_achievements(self) -> Dict[str, Achievement]:
        """Initialize all available achievements"""
        achievements = [
            # Speed achievements
            Achievement("speed_1", "Velocity Rookie", "Alcanza 30 WPM", "⚡", 30, category="speed"),
            Achievement("speed_2", "Code Runner", "Alcanza 50 WPM", "🚀", 50, category="speed"),
            Achievement("speed_3", "Terminal Velocity", "Alcanza 80 WPM", "💨", 80, category="speed"),
            Achievement("speed_4", "Keyboard Ninja", "Alcanza 100 WPM", "🥷", 100, category="speed"),
            
            # Level achievements
            Achievement("level_5", "Scripter", "Alcanza nivel 5", "📜", 5, category="level"),
            Achievement("level_10", "Developer", "Alcanza nivel 10", "💻", 10, category="level"),
            Achievement("level_20", "Senior Dev", "Alcanza nivel 20", "🎯", 20, category="level"),
            Achievement("level_50", "Tech Lead", "Alcanza nivel 50", "👑", 50, category="level"),
            
            # Accuracy achievements
            Achievement("accuracy_1", "Precise Coder", "Completa 10 desafíos perfectos", "🎯", 10, category="accuracy"),
            Achievement("accuracy_2", "Zero Tolerance", "Completa 50 desafíos perfectos", "✨", 50, category="accuracy"),
            Achievement("accuracy_3", "Flawless Execution", "Completa 100 desafíos perfectos", "💎", 100, category="accuracy"),
            
            # Survival achievements
            Achievement("survival_1", "Survivor", "Sobrevive a 10 desafíos en modo Survival", "🛡️", 10, category="survival"),
            Achievement("survival_2", "Unbreakable", "Sobrevive a 50 desafíos en modo Survival", "💪", 50, category="survival"),
            Achievement("survival_3", "Immortal", "Alcanza score 500 en Survival", "👹", 500, category="survival"),
            
            # Combo achievements
            Achievement("combo_1", "Combo Starter", "Alcanza combo x10", "🔥", 10, category="combo"),
            Achievement("combo_2", "Combo Master", "Alcanza combo x25", "⚡", 25, category="combo"),
            Achievement("combo_3", "Unstoppable", "Alcanza combo x50", "💥", 50, category="combo"),
            
            # Practice achievements
            Achievement("practice_1", "Dedicated", "Completa 100 desafíos totales", "📚", 100, category="practice"),
            Achievement("practice_2", "Persistent", "Completa 500 desafíos totales", "🏆", 500, category="practice"),
            Achievement("practice_3", "Grandmaster", "Completa 1000 desafíos totales", "🌟", 1000, category="practice"),
            
            # Python mastery achievements
            Achievement("python_basics", "Python Basics", "Domina conceptos básicos", "🐍", 1, category="mastery"),
            Achievement("python_oop", "OOP Master", "Domina POO en Python", "🏗️", 1, category="mastery"),
            Achievement("python_data", "Data Wizard", "Domina estructuras de datos", "📊", 1, category="mastery"),
            Achievement("python_advanced", "Pythonista", "Domina conceptos avanzados", "🧙", 1, category="mastery"),
        ]
        
        return {ach.id: ach for ach in achievements}
    
    def check_achievements(self, player_data: dict) -> List[Achievement]:
        """Check if any new achievements were unlocked"""
        newly_unlocked = []
        
        # Speed achievements
        if player_data.get("fastest_wpm", 0) >= 30 and not self.achievements["speed_1"].unlocked:
            newly_unlocked.append(self._unlock_achievement("speed_1"))
        if player_data.get("fastest_wpm", 0) >= 50 and not self.achievements["speed_2"].unlocked:
            newly_unlocked.append(self._unlock_achievement("speed_2"))
        if player_data.get("fastest_wpm", 0) >= 80 and not self.achievements["speed_3"].unlocked:
            newly_unlocked.append(self._unlock_achievement("speed_3"))
        if player_data.get("fastest_wpm", 0) >= 100 and not self.achievements["speed_4"].unlocked:
            newly_unlocked.append(self._unlock_achievement("speed_4"))
        
        # Level achievements
        level = player_data.get("level", 1)
        if level >= 5 and not self.achievements["level_5"].unlocked:
            newly_unlocked.append(self._unlock_achievement("level_5"))
        if level >= 10 and not self.achievements["level_10"].unlocked:
            newly_unlocked.append(self._unlock_achievement("level_10"))
        if level >= 20 and not self.achievements["level_20"].unlocked:
            newly_unlocked.append(self._unlock_achievement("level_20"))
        if level >= 50 and not self.achievements["level_50"].unlocked:
            newly_unlocked.append(self._unlock_achievement("level_50"))
        
        # Accuracy achievements
        perfect = self.stats.get("perfect_challenges", 0)
        if perfect >= 10 and not self.achievements["accuracy_1"].unlocked:
            newly_unlocked.append(self._unlock_achievement("accuracy_1"))
        if perfect >= 50 and not self.achievements["accuracy_2"].unlocked:
            newly_unlocked.append(self._unlock_achievement("accuracy_2"))
        if perfect >= 100 and not self.achievements["accuracy_3"].unlocked:
            newly_unlocked.append(self._unlock_achievement("accuracy_3"))
        
        # Survival achievements
        survival_score = player_data.get("best_survival", 0)
        if survival_score >= 100 and not self.achievements["survival_1"].unlocked:
            newly_unlocked.append(self._unlock_achievement("survival_1"))
        if survival_score >= 300 and not self.achievements["survival_2"].unlocked:
            newly_unlocked.append(self._unlock_achievement("survival_2"))
        if survival_score >= 500 and not self.achievements["survival_3"].unlocked:
            newly_unlocked.append(self._unlock_achievement("survival_3"))
        
        # Combo achievements
        combo = self.stats.get("highest_combo", 0)
        if combo >= 10 and not self.achievements["combo_1"].unlocked:
            newly_unlocked.append(self._unlock_achievement("combo_1"))
        if combo >= 25 and not self.achievements["combo_2"].unlocked:
            newly_unlocked.append(self._unlock_achievement("combo_2"))
        if combo >= 50 and not self.achievements["combo_3"].unlocked:
            newly_unlocked.append(self._unlock_achievement("combo_3"))
        
        # Practice achievements
        total = self.stats.get("total_challenges", 0)
        if total >= 100 and not self.achievements["practice_1"].unlocked:
            newly_unlocked.append(self._unlock_achievement("practice_1"))
        if total >= 500 and not self.achievements["practice_2"].unlocked:
            newly_unlocked.append(self._unlock_achievement("practice_2"))
        if total >= 1000 and not self.achievements["practice_3"].unlocked:
            newly_unlocked.append(self._unlock_achievement("practice_3"))
        
        return newly_unlocked
    
    def _unlock_achievement(self, achievement_id: str) -> Achievement:
        """Unlock an achievement"""
        ach = self.achievements[achievement_id]
        ach.unlocked = True
        ach.unlock_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return ach
    
    def get_unlocked_count(self) -> int:
        """Get number of unlocked achievements"""
        return sum(1 for ach in self.achievements.values() if ach.unlocked)
    
    def get_total_count(self) -> int:
        """Get total number of achievements"""
        return len(self.achievements)
    
    def get_achievements_by_category(self, category: str) -> List[Achievement]:
        """Get all achievements in a category"""
        return [ach for ach in self.achievements.values() if ach.category == category]
    
    def to_dict(self) -> dict:
        """Convert achievements to dictionary for saving"""
        return {
            "achievements": {
                ach_id: asdict(ach) for ach_id, ach in self.achievements.items()
            },
            "stats": {
                "total_challenges": self.stats["total_challenges"],
                "perfect_challenges": self.stats["perfect_challenges"],
                "total_keystrokes": self.stats["total_keystrokes"],
                "errors_made": self.stats["errors_made"],
                "fastest_wpm": self.stats["fastest_wpm"],
                "total_xp_earned": self.stats["total_xp_earned"],
                "survival_runs": self.stats["survival_runs"],
                "highest_combo": self.stats["highest_combo"],
                "time_played_seconds": self.stats["time_played_seconds"],
                "python_concepts_mastered": list(self.stats["python_concepts_mastered"])
            }
        }
    
    def from_dict(self, data: dict):
        """Load achievements from dictionary"""
        if "achievements" in data:
            for ach_id, ach_data in data["achievements"].items():
                if ach_id in self.achievements:
                    self.achievements[ach_id].unlocked = ach_data["unlocked"]
                    self.achievements[ach_id].unlock_date = ach_data.get("unlock_date", "")
        
        if "stats" in data:
            self.stats.update(data["stats"])
            # Convert list back to set for python_concepts_mastered
            if "python_concepts_mastered" in self.stats:
                self.stats["python_concepts_mastered"] = set(self.stats["python_concepts_mastered"])