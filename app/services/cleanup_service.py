from __future__ import annotations

from typing import Dict, List, Optional
from textwrap import shorten
import logging

from app.db.supabase_client import get_client, list_keywords
from app.services.content_extractor import extract_main_text
from app.llm.openrouter_client import get_openrouter_client
from app.location.locations import MALAYSIA_DISTRICTS, normalize_location
from app.utils.media_name import infer_media_name_from_url


logger = logging.getLogger(__name__)


def _all_allowed_keywords() -> List[str]:
    return [k["keyword"] for k in list_keywords()]


SYSTEM_PROMPT = """
You clean and standardize metadata for Malaysian public health monitoring.
Given an article's URL, site text, and current fields, return a STRICT JSON object with keys:
- media_name: The site/publication name (e.g., The Star, Malay Mail, X, Reddit). Must be non-empty.
- keyword: ONE best keyword from the provided allowed list. Choose the single most relevant keyword; if none fits well, pick the closest.
- state: One of the official Malaysian states or federal territories.
- district: One of that state's districts (if reasonably inferable), else null.
- summary: ONE sentence summary (<= 30 words), neutral and factual, describing the main health-related point.

Always produce exactly this JSON shape:
{"media_name": "...", "keyword": "...", "state": "... or null", "district": "... or null", "summary": "..."}
"""


def _build_user_prompt(url: str, text: str, allowed_keywords: List[str], current_media: Optional[str]) -> str:
    allowed = ", ".join(sorted(allowed_keywords)) or "(none provided)"
    context = shorten(text, width=8000, placeholder=" ...") if text else ""
    return (
        f"URL: {url}\n\n"
        f"Allowed keywords: [{allowed}]\n\n"
        f"Current media_name (may be wrong or missing): {current_media or 'null'}\n\n"
        f"Article text (truncated):\n{context}\n\n"
        "Return ONLY the JSON object."
    )


def _llm_clean(url: str, text: str, allowed_keywords: List[str], current_media: Optional[str]) -> Optional[Dict]:
    from app.config import get_settings

    settings = get_settings()
    client = get_openrouter_client()
    prompt = _build_user_prompt(url, text, allowed_keywords, current_media)
    completion = client.chat.completions.create(
        model=settings.openrouter_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    content = completion.choices[0].message.content.strip()
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("` ")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
    import json

    try:
        data = json.loads(cleaned)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _fill_defaults(url: str, guess: Dict, allowed_keywords: List[str], text: str) -> Dict:
    # media_name fallback from URL
    if not guess.get("media_name"):
        guess["media_name"] = infer_media_name_from_url(url) or "Unknown"

    # keyword must be from allowed list; choose first if not provided
    kw = guess.get("keyword")
    if not kw or kw not in allowed_keywords:
        guess["keyword"] = allowed_keywords[0] if allowed_keywords else "general"

    # normalize location; if none provided, fallback to general 'Malaysia'
    state = guess.get("state")
    district = guess.get("district")
    n_state, n_district = normalize_location(state, district)
    if not n_state and not n_district:
        guess["state"] = "Malaysia"
        guess["district"] = None
    else:
        guess["state"] = n_state or (list(MALAYSIA_DISTRICTS.keys())[0])
        if n_state and not n_district and MALAYSIA_DISTRICTS.get(n_state):
            guess["district"] = MALAYSIA_DISTRICTS[n_state][0]
        elif n_district:
            guess["district"] = n_district
        else:
            # pick a default district for the chosen/default state
            default_state = guess["state"]
            guess["district"] = (MALAYSIA_DISTRICTS[default_state][0]) if MALAYSIA_DISTRICTS.get(default_state) else None

    # ensure summary exists (one sentence). If missing, make a short extractive sentence.
    summary = (guess.get("summary") or "").strip()
    if not summary:
        # naive first sentence extraction
        snippet = (text or "").strip()
        end_idx = -1
        for sep in [". ", "! ", "? "]:
            idx = snippet.find(sep)
            if idx != -1:
                end_idx = idx + 1
                break
        first_sentence = snippet[: end_idx if end_idx != -1 else 160].strip()
        if first_sentence:
            summary = first_sentence
        else:
            summary = "Summary unavailable."
        guess["summary"] = summary

    return guess


def clean_mentions_with_llm(limit: int = 50) -> Dict[str, int]:
    """For mentions with missing/dirty media_name, keywords, or location, fetch body,
    call LLM once per row to fill media_name, ONE keyword (from allowed list), and location.
    Writes cleaned values back to DB. Returns counts.
    """
    client = get_client()
    allowed_keywords = _all_allowed_keywords()
    # Select rows that need cleaning: missing media_name or empty keywords or null location or null summary
    resp = (
        client.table("mentions")
        .select("*")
        .or_("media_name.is.null,keywords.is.null,location.is.null,summary.is.null")
        .limit(limit)
        .execute()
    )
    rows = resp.data or []

    counts = {"processed": 0, "updated": 0}
    for row in rows:
        counts["processed"] += 1
        url = row.get("link")
        text = extract_main_text(url) or ""
        # Determine emptiness (also treat empty strings/arrays/objects as empty)
        media_empty = (row.get("media_name") or "").strip() == ""
        keywords_empty = not row.get("keywords") or len(row.get("keywords") or []) == 0
        location_empty = not row.get("location") or row.get("location") == {}
        summary_empty = (row.get("summary") or "").strip() == ""
        if not (media_empty or keywords_empty or location_empty or summary_empty):
            continue
        guess = _llm_clean(url or "", text, allowed_keywords, row.get("media_name")) or {}
        guess = _fill_defaults(url or "", guess, allowed_keywords, text)

        # Only update the fields that are empty
        update_payload: Dict[str, object] = {}
        if media_empty:
            update_payload["media_name"] = guess["media_name"]
        if keywords_empty:
            update_payload["keywords"] = [guess["keyword"]]
        if location_empty:
            update_payload["location"] = {"state": guess["state"], "district": guess["district"]}
        if summary_empty:
            update_payload["summary"] = guess.get("summary", "")

        if update_payload:
            try:
                client.table("mentions").update(update_payload).eq("id", row["id"]).execute()
                counts["updated"] += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to update cleaned mention %s: %s", row.get("id"), exc)

    return counts


