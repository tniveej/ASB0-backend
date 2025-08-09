from __future__ import annotations

from typing import List


def choose_best_keyword(text: str, allowed_keywords: List[str]) -> str:
    if not allowed_keywords:
        return "general"
    lowered = (text or "").lower()
    for kw in allowed_keywords:
        if kw and kw.lower() in lowered:
            return kw
    return allowed_keywords[0]


