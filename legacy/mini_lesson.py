"""Mini-lesson shown before a challenge — Phase 2.1."""
from __future__ import annotations
from typing import Any, Optional


def build_mini_lesson(
    challenge: Any = None,
    concept: str = "",
    tips_system: Any = None,
    content: Any = None,
) -> dict:
    """
    Returns {title, body, example, compact} for UI labels.
    Prefers challenge.explanation, then content tips, then tips_system.
    """
    concept = (concept or getattr(challenge, "concept", "") or "").strip()
    title = f"◈ MINI LECCION · {concept}" if concept else "◈ MINI LECCION"

    body = ""
    if challenge is not None:
        body = (getattr(challenge, "explanation", "") or "").strip()
        if not body:
            body = (getattr(challenge, "hint", "") or "").strip()

    if not body and content is not None and concept:
        try:
            body = (content.get_explanation(concept, challenge) or "").strip()
        except Exception:
            body = ""

    tip = ""
    if tips_system is not None and concept:
        try:
            tip = (tips_system.get_tip_for_concept(concept) or "").strip()
        except Exception:
            tip = ""

    if tip and tip not in body:
        if body:
            body = f"{body}\n\n💡 {tip}"
        else:
            body = f"💡 {tip}"

    if not body:
        body = "Observa el patron, escribe con precision y usa Pista si te bloqueas."

    example = ""
    if challenge is not None:
        prompt = (getattr(challenge, "prompt", "") or "").strip()
        ctype = getattr(challenge, "challenge_type", "full")
        if ctype == "blank" and prompt:
            example = f"Plantilla: {prompt}"
        elif ctype != "blank":
            text = (getattr(challenge, "text", "") or "").strip()
            if text and len(text) <= 60:
                example = f"Objetivo: {text}"

    compact = body.split("\n")[0][:120]

    return {
        "title": title,
        "body": body,
        "example": example,
        "compact": compact,
        "concept": concept,
    }
