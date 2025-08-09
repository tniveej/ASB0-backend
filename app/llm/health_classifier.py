from __future__ import annotations

from typing import Optional
import json

from app.config import get_settings
from app.llm.openrouter_client import get_openrouter_client


SYSTEM_PROMPT = """
You are a strict binary classifier. Given a news item's title and summary, decide if it is HEALTH-RELATED (public health, diseases, outbreaks, vaccines, hospitals, environment affecting health, etc.) in Malaysia or generally relevant to Malaysian public health.
Respond with STRICT JSON: {"is_health": true|false} and nothing else.
"""


def is_health_related(title: str, summary: str) -> Optional[bool]:
    settings = get_settings()
    try:
        client = get_openrouter_client()
    except Exception:
        # If no LLM configured, default to True to avoid missing items
        return True

    user_prompt = (
        f"Title: {title or ''}\n\n"
        f"Summary: {summary or ''}\n\n"
        "Answer as strict JSON only."
    )

    try:
        completion = client.chat.completions.create(
            model=settings.openrouter_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
        )
        if not completion or not getattr(completion, "choices", None):
            return None
        first = completion.choices[0]
        message = getattr(first, "message", None)
        content = getattr(message, "content", None)
        if not content:
            return None
        raw = content.strip()
        if raw.startswith("```"):
            raw = raw.strip("` ")
            if raw.startswith("json"):
                raw = raw[4:].strip()
        data = json.loads(raw)
        val = data.get("is_health") if isinstance(data, dict) else None
        if isinstance(val, bool):
            return val
        # Accept common string forms
        if isinstance(val, str):
            return val.lower() in {"true", "yes", "y"}
        return None
    except Exception:
        return None


def classify_batch(items: list[dict]) -> list[bool]:
    """Classify up to ~20 items per request to reduce costs.
    Items: [{"title": str, "summary": str}]
    Returns a list of booleans (default True on failure for recall).
    """
    settings = get_settings()
    try:
        client = get_openrouter_client()
    except Exception:
        return [True] * len(items)

    # Build a compact JSON array to send once
    payload = json.dumps(
        [
            {"title": (it.get("title") or ""), "summary": (it.get("summary") or "")}
            for it in items
        ]
    )

    system = (
        "You are a strict binary classifier. For each entry in the provided JSON array of {title, summary},"
        " decide if it is HEALTH-RELATED in Malaysia or relevant to Malaysian public health."
        " Respond ONLY with a JSON array of booleans, same order as input (e.g., [true,false,...])."
    )

    try:
        completion = client.chat.completions.create(
            model=settings.openrouter_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": payload},
            ],
            temperature=0.0,
        )
        if not completion or not getattr(completion, "choices", None):
            return [True] * len(items)
        first = completion.choices[0]
        message = getattr(first, "message", None)
        content = getattr(message, "content", None)
        if not content:
            return [True] * len(items)
        raw = content.strip()
        if raw.startswith("```"):
            raw = raw.strip("` ")
            if raw.startswith("json"):
                raw = raw[4:].strip()
        data = json.loads(raw)
        if isinstance(data, list):
            return [bool(x) for x in data][: len(items)]
        return [True] * len(items)
    except Exception:
        return [True] * len(items)


