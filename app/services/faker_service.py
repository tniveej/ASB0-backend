from __future__ import annotations

from typing import Dict, List, Optional
from datetime import datetime, timezone
import json
import random

from app.llm.openrouter_client import get_openrouter_client
from app.config import get_settings
from app.utils.media_name import infer_media_name_from_url
from app.location.locations import MALAYSIA_DISTRICTS, normalize_location


SYSTEM_PROMPT = """
You generate realistic but fictional Malaysian health-related posts and news items. It can also be social media posts from social media sites like X and Instagram. Prefer social media over news articles. if it is a social media post, make sure the language is more casual. You can also generate in malay.
Return STRICT JSON (no prose) as an array of objects with these keys per item:
- date: ISO date (YYYY-MM-DD), within the current year
- data_source: either "News Outlet", "Social Media" or "Web Search"
- headline: concise title
- summary: 1-2 sentence summary
- image_url: plausible URL (may be null)
- link: plausible unique URL (may be null)
- media_type: "news article" | "social media" | "web article"
- media_outlet: site/publication/outlet name
- media_name: same as publication name (e.g., The Star, Malay Mail, X)
- status: "unverified"
- keywords: array with EXACTLY ONE keyword chosen from the allowed list provided
- engagement: integer (0-10000 range)
- location: object { state: one of Malaysian states or "Malaysia", district: district or null }
"""


def _build_user_prompt(count: int, allowed_keywords: List[str]) -> str:
    year = datetime.utcnow().year
    allowed = ", ".join(sorted(allowed_keywords)) or "(none)"
    return (
        f"Generate {count} items of Malaysian health-related posts/news, JSON array only.\n"
        f"Allowed keywords (choose exactly ONE per item): [{allowed}]\n"
        f"Dates must be in {year}."
    )


def _coerce_item(item: Dict, allowed_keywords: List[str]) -> Optional[Dict]:
    # Coerce fields and provide fallbacks
    today = datetime.utcnow().date()
    year = today.year
    date_str = item.get("date") or str(today)
    try:
        d = datetime.fromisoformat(date_str).date()
        if d.year != year:
            d = today
        date_str = d.isoformat()
    except Exception:
        date_str = today.isoformat()

    headline = (item.get("headline") or "").strip() or "Health update in Malaysia"
    summary = (item.get("summary") or "").strip() or "A brief update related to public health in Malaysia."
    link = (item.get("link") or "").strip() or f"https://example.com/{random.randint(100000,999999)}"
    media_name = (item.get("media_name") or "").strip() or infer_media_name_from_url(link) or "Unknown"

    data_source = item.get("data_source") or ("News Outlet" if "http" in link else "Web Search")
    media_type = item.get("media_type") or ("news article" if data_source == "News Outlet" else "web article")
    media_outlet = item.get("media_outlet") or media_name
    status = item.get("status") or "unverified"
    image_url = item.get("image_url")

    kws = item.get("keywords") or []
    if isinstance(kws, list) and kws:
        kw = kws[0]
    else:
        kw = allowed_keywords[0] if allowed_keywords else "general"
    if kw not in allowed_keywords and allowed_keywords:
        kw = allowed_keywords[0]

    # Location normalize; fallback to Malaysia
    loc = item.get("location") or {}
    state = loc.get("state") if isinstance(loc, dict) else None
    district = loc.get("district") if isinstance(loc, dict) else None
    n_state, n_district = normalize_location(state, district)
    if not n_state and not n_district:
        n_state, n_district = "Malaysia", None

    engagement = item.get("engagement")
    try:
        engagement = int(engagement) if engagement is not None else random.randint(0, 5000)
    except Exception:
        engagement = random.randint(0, 5000)

    return {
        "date": date_str,
        "data_source": data_source,
        "headline": headline,
        "summary": summary,
        "image_url": image_url,
        "link": link,
        "media_type": media_type,
        "media_outlet": media_outlet,
        "media_name": media_name,
        "status": status,
        "keywords": [kw],
        "engagement": engagement,
        "location": {"state": n_state, "district": n_district},
    }


def generate_fake_mentions(count: int, allowed_keywords: List[str]) -> List[Dict]:
    settings = get_settings()
    client = get_openrouter_client()
    prompt = _build_user_prompt(count, allowed_keywords)
    try:
        completion = client.chat.completions.create(
            model=settings.openrouter_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        if not completion or not getattr(completion, "choices", None):
            return []
        first = completion.choices[0]
        message = getattr(first, "message", None)
        content = getattr(message, "content", None)
        if not content:
            return []
        raw = content.strip()
        if raw.startswith("```"):
            raw = raw.strip("` ")
            if raw.startswith("json"):
                raw = raw[4:].strip()
        data = json.loads(raw)
        if not isinstance(data, list):
            return []
    except Exception:
        return []

    coerced: List[Dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        coerced_item = _coerce_item(item, allowed_keywords)
        if coerced_item:
            coerced.append(coerced_item)
    return coerced


