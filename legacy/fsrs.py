"""
FSRS-lite for KeyMaster
Simplified Free Spaced Repetition Scheduler (inspired by FSRS-4.5 / Anki).

Tracks per-concept:
  difficulty D in [1, 10]
  stability  S in days (>0)
  last_review ISO date
  next_review ISO date
  reps, lapses

Grade mapping from KeyMaster events:
  fail              -> 1 (Again)
  success + errors  -> 2 (Hard)
  success           -> 3 (Good)
  success + perfect -> 4 (Easy)

Target retention R = 0.9 (schedule when predicted recall hits 90%).
"""
from __future__ import annotations
from datetime import datetime, timedelta, date
from math import exp
from typing import Optional, Tuple

# FSRS-4.5 default weights (core subset for S/D updates)
W = (
    0.40255,  # 0  initial stability again
    1.18385,  # 1  initial stability hard
    3.173,    # 2  initial stability good
    15.69105, # 3  initial stability easy
    7.1949,   # 4  initial difficulty
    0.5345,   # 5  difficulty delta
    1.4604,   # 6  difficulty mean reversion (reserved)
    0.0046,   # 7  mean reversion target factor
    1.54575,  # 8  stability after success factor
    0.119,    # 9  stability after success decay
    1.01925,  # 10 stability after success power
    1.9395,   # 11 fail stability factor
    0.11,     # 12 fail stability decay on D
    0.29605,  # 13 fail stability power on S
    2.2698,   # 14 hard penalty
    0.2312,   # 15 easy bonus
    2.9898,   # 16 reserved
)

REQUESTED_RETENTION = 0.9
MAX_INTERVAL = 365.0
MIN_STABILITY = 0.1


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def retrievability(elapsed_days: float, stability: float) -> float:
    """R(t) = (1 + t/(9*S))^(-1)  — FSRS-4.5 formula."""
    s = max(MIN_STABILITY, float(stability or MIN_STABILITY))
    t = max(0.0, float(elapsed_days))
    return (1.0 + t / (9.0 * s)) ** -1.0


def next_interval(stability: float, retention: float = REQUESTED_RETENTION) -> float:
    """Days until R drops to target retention: t = 9*S*(1/R - 1)."""
    s = max(MIN_STABILITY, float(stability or MIN_STABILITY))
    r = _clamp(float(retention), 0.7, 0.97)
    t = 9.0 * s * (1.0 / r - 1.0)
    return _clamp(t, 1.0, MAX_INTERVAL)


def _init_stability(grade: int) -> float:
    g = _clamp(int(grade), 1, 4)
    return max(MIN_STABILITY, W[g - 1])


def _init_difficulty(grade: int) -> float:
    g = _clamp(int(grade), 1, 4)
    d = W[4] - (g - 3) * W[5]
    return _clamp(d, 1.0, 10.0)


def _next_difficulty(d: float, grade: int) -> float:
    g = _clamp(int(grade), 1, 4)
    delta = -W[5] * (g - 3)
    dn = d + delta * (10.0 - d) / 9.0
    dn = W[7] * _init_difficulty(3) + (1.0 - W[7]) * dn
    return _clamp(dn, 1.0, 10.0)


def _next_stability_success(d: float, s: float, r: float, grade: int) -> float:
    g = _clamp(int(grade), 1, 4)
    hard_pen = W[14] if g == 2 else 1.0
    easy_bon = W[15] if g == 4 else 1.0
    factor = (
        exp(W[8])
        * ((11.0 - d) ** W[9])
        * (s ** -W[10])
        * (exp((1.0 - r) * W[10]) - 1.0)
        * hard_pen
        * easy_bon
    )
    return max(s, s * (1.0 + factor))


def _next_stability_fail(d: float, s: float, r: float) -> float:
    s_fail = (
        W[11]
        * (d ** -W[12])
        * ((s + 1.0) ** W[13] - 1.0)
        * exp((1.0 - r) * W[8])
    )
    return max(MIN_STABILITY, min(s_fail, s))


def grade_from_result(success: bool, perfect: bool = False, errors: int = 0) -> int:
    if not success:
        return 1
    if perfect and errors <= 0:
        return 4
    if errors and errors > 0:
        return 2
    return 3


def ensure_card(st: dict) -> dict:
    """Normalize concept_stats entry with FSRS fields."""
    st.setdefault("attempts", 0)
    st.setdefault("errors", 0)
    st.setdefault("successes", 0)
    st.setdefault("fails", 0)
    st.setdefault("fsrs_difficulty", None)
    st.setdefault("fsrs_stability", None)
    st.setdefault("fsrs_reps", 0)
    st.setdefault("fsrs_lapses", 0)
    st.setdefault("last_reviewed", None)
    st.setdefault("next_review", None)
    st.setdefault("interval_days", 0)
    st.setdefault("srs_step", 0)
    st.setdefault("consecutive_correct", 0)
    return st


def review(
    st: dict,
    success: bool,
    perfect: bool = False,
    errors: int = 0,
    today: Optional[date] = None,
    retention: float = REQUESTED_RETENTION,
) -> dict:
    """Apply one FSRS review to concept stats dict (mutates and returns st)."""
    st = ensure_card(st)
    today = today or datetime.now().date()
    grade = grade_from_result(success, perfect=perfect, errors=errors)

    elapsed = 0.0
    last = st.get("last_reviewed")
    if last:
        try:
            last_d = datetime.strptime(str(last)[:10], "%Y-%m-%d").date()
            elapsed = max(0.0, float((today - last_d).days))
        except Exception:
            elapsed = float(st.get("interval_days") or 0)

    d = st.get("fsrs_difficulty")
    s = st.get("fsrs_stability")
    reps = int(st.get("fsrs_reps") or 0)

    if d is None or s is None or reps == 0:
        d = _init_difficulty(grade)
        s = _init_stability(grade)
        if grade == 1:
            st["fsrs_lapses"] = int(st.get("fsrs_lapses") or 0) + 1
    else:
        d = float(d)
        s = float(s)
        r = retrievability(elapsed, s)
        if grade == 1:
            s = _next_stability_fail(d, s, r)
            d = _next_difficulty(d, grade)
            st["fsrs_lapses"] = int(st.get("fsrs_lapses") or 0) + 1
        else:
            s = _next_stability_success(d, s, r, grade)
            d = _next_difficulty(d, grade)

    st["fsrs_difficulty"] = round(float(d), 4)
    st["fsrs_stability"] = round(float(s), 4)
    st["fsrs_reps"] = reps + 1

    interval = next_interval(s, retention=retention)
    if grade == 1:
        interval = max(1.0, min(interval, 3.0))
    interval_days = max(1, int(round(interval)))
    st["interval_days"] = interval_days
    st["next_review"] = (today + timedelta(days=interval_days)).isoformat()
    st["last_reviewed"] = today.isoformat()
    st["consecutive_correct"] = 0 if grade == 1 else int(st.get("consecutive_correct") or 0) + 1
    if interval_days <= 1:
        st["srs_step"] = 0
    elif interval_days <= 3:
        st["srs_step"] = 1
    elif interval_days <= 7:
        st["srs_step"] = 2
    elif interval_days <= 14:
        st["srs_step"] = 3
    elif interval_days <= 30:
        st["srs_step"] = 4
    else:
        st["srs_step"] = 5
    return st


def is_due(st: dict, today: Optional[date] = None) -> Tuple[bool, float]:
    """Return (due?, retrievability_now)."""
    today = today or datetime.now().date()
    st = ensure_card(st)
    s = st.get("fsrs_stability")
    last = st.get("last_reviewed")
    nr = st.get("next_review")
    elapsed = 0.0
    if last:
        try:
            last_d = datetime.strptime(str(last)[:10], "%Y-%m-%d").date()
            elapsed = max(0.0, float((today - last_d).days))
        except Exception:
            elapsed = 0.0
    r = retrievability(elapsed, float(s)) if s else 0.0
    if nr:
        try:
            d = datetime.strptime(str(nr)[:10], "%Y-%m-%d").date()
            return (d <= today, r)
        except Exception:
            pass
    if st.get("attempts", 0) > 0:
        return True, r
    return False, 1.0


def schedule_summary(st: dict, today: Optional[date] = None) -> dict:
    today = today or datetime.now().date()
    due, r = is_due(st, today)
    nr = st.get("next_review")
    days_left = 0
    status = "pendiente"
    if nr:
        try:
            d = datetime.strptime(str(nr)[:10], "%Y-%m-%d").date()
            days_left = (d - today).days
            if days_left < 0:
                status = f"vencido {-days_left}d"
            elif days_left == 0:
                status = "hoy"
            else:
                status = f"en {days_left}d"
        except Exception:
            status = "?"
            days_left = 999
    return {
        "status": status,
        "days_left": days_left,
        "interval": st.get("interval_days", 0),
        "step": st.get("srs_step", 0),
        "next_review": nr,
        "stability": st.get("fsrs_stability"),
        "difficulty": st.get("fsrs_difficulty"),
        "retrievability": round(r, 3),
        "due": due,
        "reps": st.get("fsrs_reps", 0),
        "lapses": st.get("fsrs_lapses", 0),
    }
