from __future__ import annotations

from typing import List
import json

from app.config import get_settings
from app.llm.openrouter_client import get_openrouter_client


def summarize_batch(items: List[dict]) -> List[str]:
    """Summarize a batch of items. Each item: {"title": str, "text": str}
    Returns a list of single-sentence summaries (<=30 words). Falls back to empty string on error.
    """
    settings = get_settings()
    try:
        client = get_openrouter_client()
    except Exception:
        # No LLM configured
        return [""] * len(items)

    payload = json.dumps(
        [{"title": it.get("title") or "", "text": it.get("text") or ""} for it in items]
    )
    system = (
        "You are a concise summarizer. For each object in the JSON array of {title, text},"
        " produce ONE neutral, factual sentence (<= 30 words) summarizing the main health-related point."
        " Respond ONLY with a JSON array of strings in the same order."
    )

    try:
        completion = client.chat.completions.create(
            model=settings.openrouter_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": payload},
            ],
            temperature=0.2,
        )
        if not completion or not getattr(completion, "choices", None):
            return [""] * len(items)
        first = completion.choices[0]
        message = getattr(first, "message", None)
        content = getattr(message, "content", None)
        if not content:
            return [""] * len(items)
        raw = content.strip()
        if raw.startswith("```"):
            raw = raw.strip("` ")
            if raw.startswith("json"):
                raw = raw[4:].strip()
        data = json.loads(raw)
        if isinstance(data, list):
            # ensure all are strings
            return [str(x) if x is not None else "" for x in data][: len(items)]
        return [""] * len(items)
    except Exception:
        return [""] * len(items)


