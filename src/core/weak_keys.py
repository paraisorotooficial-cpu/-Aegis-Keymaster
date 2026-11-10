"""
Weak-key tracking and adaptive review drill generation.
Collects per-key error statistics and produces short targeted exercises.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class KeyStats:
    attempts: int = 0
    errors: int = 0
    latency_total: float = 0.0
    latency_samples: int = 0

    @property
    def error_rate(self) -> float:
        if self.attempts == 0:
            return 0.0
        return self.errors / self.attempts

    @property
    def accuracy(self) -> float:
        return 100.0 * (1.0 - self.error_rate)

    @property
    def avg_latency(self) -> float:
        """Mean seconds since the previous keystroke (0 when unknown)."""
        if self.latency_samples == 0:
            return 0.0
        return self.latency_total / self.latency_samples

    def to_dict(self) -> dict:
        return {
            "attempts": self.attempts,
            "errors": self.errors,
            "latency_total": round(self.latency_total, 4),
            "latency_samples": self.latency_samples,
        }

    @classmethod
    def from_dict(cls, data: dict) -> KeyStats:
        return cls(
            attempts=int(data.get("attempts", 0)),
            errors=int(data.get("errors", 0)),
            latency_total=float(data.get("latency_total", 0.0)),
            latency_samples=int(data.get("latency_samples", 0)),
        )


class WeakKeyTracker:
    """
    Tracks which keys the user misses most often.
    Call `record_attempt(expected, typed)` for every character comparison,
    or `record_session(target, typed)` after a full exercise.
    """

    def __init__(self):
        self._stats: dict[str, KeyStats] = defaultdict(KeyStats)
        self._total_errors = 0
        self._total_attempts = 0

    # ── Recording ────────────────────────────

    def record_attempt(self, expected: str, got: str):
        """Record a single character attempt. Case is preserved so Shift errors stay visible."""
        key = expected if expected else " "

        st = self._stats[key]
        st.attempts += 1
        self._total_attempts += 1
        if got != expected:
            st.errors += 1
            self._total_errors += 1

    def record_session(self, target: str, typed: str):
        """
        Record a full exercise by aligning target and typed character-by-character.
        """
        n = min(len(target), len(typed))
        for i in range(n):
            self.record_attempt(target[i], typed[i])
        # Characters not yet typed are ignored (not errors)

    def ingest_log(self, log: list[dict]) -> None:
        """Consume a keystroke log (see TypingTestSession.keystroke_log).

        Backspaces are skipped; per-key latency is derived from the offset
        between consecutive character attempts.
        """
        previous_offset: float | None = None
        for entry in log:
            if entry.get("is_backspace"):
                continue
            expected = str(entry.get("expected", ""))
            if not expected:
                continue
            offset = float(entry.get("offset", 0.0))
            st = self._stats[expected]
            st.attempts += 1
            self._total_attempts += 1
            if not entry.get("correct", False):
                st.errors += 1
                self._total_errors += 1
            if previous_offset is not None:
                latency = offset - previous_offset
                if latency >= 0:
                    st.latency_total += latency
                    st.latency_samples += 1
            previous_offset = offset

    def reset(self):
        self._stats.clear()
        self._total_errors = 0
        self._total_attempts = 0

    @classmethod
    def from_dict(cls, data: dict[str, dict]) -> WeakKeyTracker:
        """Rebuild a tracker from persisted {key: {attempts, errors, ...}} stats."""
        tracker = cls()
        for key, entry in data.items():
            stats = KeyStats.from_dict(entry)
            tracker._stats[key] = stats
            tracker._total_attempts += stats.attempts
            tracker._total_errors += stats.errors
        return tracker

    # ── Queries ──────────────────────────────

    def weak_keys(self, top_n: int = 8, min_attempts: int = 3) -> list[tuple[str, float, int]]:
        """
        Return the weakest keys as (key, error_rate, attempts),
        sorted by error_rate descending. Only keys with enough data.
        """
        candidates = []
        for key, st in self._stats.items():
            if st.attempts >= min_attempts and st.errors > 0:
                candidates.append((key, st.error_rate, st.attempts))
        candidates.sort(key=lambda x: (-x[1], -x[2]))
        return candidates[:top_n]

    def key_stats(self, key: str) -> KeyStats:
        return self._stats.get(key, KeyStats())

    def all_stats(self) -> dict[str, KeyStats]:
        return dict(self._stats)

    def summary(self) -> str:
        weak = self.weak_keys(top_n=5, min_attempts=2)
        if not weak:
            return "No weak keys detected yet"
        parts = [f"{k!r} ({rate*100:.0f}%)" for k, rate, _ in weak]
        return "Weak: " + ", ".join(parts)

    def has_data(self) -> bool:
        return any(st.errors > 0 for st in self._stats.values())

    # ── Drill generation ─────────────────────

    def generate_drill(self, length: int = 70, top_n: int = 6) -> str:
        """
        Build a short exercise that heavily features the user's weakest keys.
        Falls back to home-row practice if there is not enough data.
        """
        weak = self.weak_keys(top_n=top_n, min_attempts=2)
        if not weak:
            # Fallback: classic home-row drill
            pool = list("asdfjkl;")
            return self._make_groups(pool, length)

        # Weight keys by error rate (higher error → more appearances)
        keys = []
        weights = []
        for key, rate, attempts in weak:
            if key == " ":
                continue
            keys.append(key)
            weights.append(max(0.15, rate) * (1 + attempts * 0.05))

        if not keys:
            keys = list("asdfjkl;")
            weights = [1.0] * len(keys)

        # Mix weak keys with a few neutral neighbors for realism
        neighbors = self._neighbors(keys)
        for n in neighbors:
            if n not in keys:
                keys.append(n)
                weights.append(0.2)

        return self._make_weighted_text(keys, weights, length)

    def _neighbors(self, keys: list[str]) -> list[str]:
        """Simple keyboard-neighbor expansion for more natural drills."""
        rows = [
            list("`1234567890-="),
            list("qwertyuiop[]\\"),
            list("asdfghjkl;'"),
            list("zxcvbnm,./"),
        ]
        found = set()
        for k in keys:
            for row in rows:
                if k in row:
                    idx = row.index(k)
                    for j in (idx - 1, idx + 1):
                        if 0 <= j < len(row):
                            found.add(row[j])
        return list(found)

    def _make_groups(self, pool: list[str], length: int) -> str:
        rng = random.Random()
        chunks = []
        total = 0
        while total < length:
            n = rng.randint(3, 5)
            chunk = "".join(rng.choice(pool) for _ in range(n))
            chunks.append(chunk)
            total += len(chunk) + 1
        return " ".join(chunks)[: length + 15].strip()

    def _make_weighted_text(self, keys: list[str], weights: list[float], length: int) -> str:
        rng = random.Random()
        # Normalize weights
        total_w = sum(weights) or 1.0
        probs = [w / total_w for w in weights]

        def pick():
            r = rng.random()
            acc = 0.0
            for k, p in zip(keys, probs, strict=True):
                acc += p
                if r <= acc:
                    return k
            return keys[-1]

        chunks = []
        total = 0
        while total < length:
            n = rng.randint(3, 5)
            chunk = "".join(pick() for _ in range(n))
            chunks.append(chunk)
            total += len(chunk) + 1
        return " ".join(chunks)[: length + 15].strip()


# Convenience: also track simple bigrams later if needed
@dataclass
class BigramStats:
    attempts: int = 0
    errors: int = 0
