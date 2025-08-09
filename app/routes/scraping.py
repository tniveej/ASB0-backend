import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter

from app.config import get_settings
from app.db.supabase_client import list_keywords, upsert_health_mention
from app.scrapers.rss_scraper import fetch_rss_entries


logger = logging.getLogger(__name__)
router = APIRouter(tags=["scraping"])


@router.post("/scrape-news")
def scrape_news():
    settings = get_settings()
    active_keywords = [k["keyword"] for k in list_keywords()]
    if not active_keywords:
        return {"message": "No active keywords configured"}

    inserted: List[dict] = []
    for feed_url in settings.rss_feeds:
        entries = fetch_rss_entries(feed_url)
        for item in entries:
            text_for_match = " ".join(
                [
                    item.get("title") or "",
                    item.get("summary") or "",
                ]
            ).lower()
            matched_keywords = [
                keyword for keyword in active_keywords if keyword.lower() in text_for_match
            ]
            if matched_keywords:
                # Map scraped item to DB schema
                date_value = (
                    item.get("published_date") or datetime.utcnow().date().isoformat()
                )

                record = {
                    "date": date_value,
                    "data_source": "News Outlet",
                    "headline": item.get("title"),
                    "summary": item.get("summary"),
                    "image_url": item.get("image_url"),
                    "link": item.get("link"),
                    "media_type": "news article",
                    "media_outlet": item.get("outlet"),
                    "media_name": item.get("outlet"),
                    "status": "unverified",
                    "keywords": matched_keywords,
                    "engagement": 0,
                }
                try:
                    inserted_item = upsert_health_mention(record)
                    inserted.append(inserted_item)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Failed to upsert %s: %s", record.get("link"), exc)

    return {"message": "scrape completed", "inserted": len(inserted)}


