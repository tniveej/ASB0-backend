from __future__ import annotations

import json
from typing import Optional, Dict

from app.config import get_settings
from app.llm.openrouter_client import get_openrouter_client
from app.location.locations import normalize_location


SYSTEM_PROMPT = """

You are a data extraction assistant. Given Malaysian news text, extract the precise state and district in Malaysia that the text most likely refers to.\n"
"Respond in STRICT JSON with keys: state, district. Use official Malaysian state and district names. If unknown, use null. Example : 

    [
  {
    "state": "Selangor",
    "district": "Petaling"
  },
  {
    "state": "Johor",
    "district": "Johor Bahru"
  },
  {
    "state": "Pulau Pinang",
    "district": "Timur Laut"
  },
  {
    "state": "Sabah",
    "district": "Kota Kinabalu"
  },
  {
    "state": "Sarawak",
    "district": "Kuching"
  },
  {
    "state": "Negeri Sembilan",
    "district": null
  },
  {
    "state": null,
    "district": null
  }
]

"""

def extract_location_with_llm(title: str, summary: str) -> Optional[Dict[str, str]]:
    settings = get_settings()
    if not settings.enable_llm_location:
        return None

    client = get_openrouter_client()
    user_prompt = (
        f"Title: {title or ''}\n\n"
        f"Summary: {summary or ''}\n\n"
        "Return JSON only."
    )

    completion = client.chat.completions.create(
        model=settings.openrouter_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    content = completion.choices[0].message.content.strip()
    try:
        data = json.loads(content)
    except Exception:
        return None

    state = data.get("state") if isinstance(data, dict) else None
    district = data.get("district") if isinstance(data, dict) else None

    norm_state, norm_district = normalize_location(state, district)
    if norm_state or norm_district:
        result: Dict[str, str] = {}
        if norm_state:
            result["state"] = norm_state
        if norm_district:
            result["district"] = norm_district
        return result
    return None


