from __future__ import annotations

from typing import Dict, List
from datetime import datetime
import logging

from app.db.supabase_client import get_client
from app.services.content_extractor import extract_main_text
from app.scrapers.location_extractor import extract_location as rules_extract
from app.llm.location_llm import extract_location_with_llm


logger = logging.getLogger(__name__)


def fetch_mentions_missing_location(limit: int = 50) -> List[Dict]:
    client = get_client()
    # location is null
    resp = client.table("mentions").select("*").is_("location", "null").limit(limit).execute()
    return resp.data or []


def update_mention_location(mention_id: str, location: Dict) -> None:
    client = get_client()
    client.table("mentions").update({"location": location}).eq("id", mention_id).execute()


def postprocess_locations(limit: int = 50) -> Dict[str, int]:
    """Load mentions without location, fetch article body, extract location via rules → LLM.
    Update rows when a location is found. Returns counts.
    """
    items = fetch_mentions_missing_location(limit=limit)
    counts = {"processed": 0, "updated": 0}
    for m in items:
        counts["processed"] += 1
        url = m.get("link")
        if not url:
            continue
        text = extract_main_text(url) or ""
        if not text:
            continue

        # Try rule-based on full body
        loc = rules_extract(text)
        if not loc:
            # LLM using title + extracted summary from body (first 500 chars)
            title = m.get("headline") or ""
            summary = text[:1000]
            loc = extract_location_with_llm(title, summary)

        if loc:
            try:
                update_mention_location(m["id"], loc)
                counts["updated"] += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed updating location for %s: %s", m.get("id"), exc)

    return counts


