import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter

from app.config import get_settings
from app.db.supabase_client import list_keywords, upsert_mention
from app.scrapers.rss_scraper import fetch_rss_entries, infer_outlet_from_link
from app.scrapers.location_extractor import extract_location
from app.llm.location_llm import extract_location_with_llm
from app.services.exa_service import search_recent_mentions


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

                # Extract location from title + summary
                location = extract_location(
                    " ".join([item.get("title") or "", item.get("summary") or ""])
                )
                if not location:
                    location = extract_location_with_llm(
                        item.get("title") or "", item.get("summary") or ""
                    )

                record = {
                    "date": date_value,
                    "data_source": "News Outlet",
                    "headline": item.get("title") or "",
                    "summary": item.get("summary"),
                    "image_url": item.get("image_url"),
                    "link": item.get("link"),
                    "media_type": "news article",
                    "media_outlet": item.get("outlet"),
                    "media_name": item.get("outlet"),
                    "status": "unverified",
                    "keywords": matched_keywords,
                    "engagement": 0,
                    "location": location,
                }
                try:
                    inserted_item = upsert_mention(record)
                    inserted.append(inserted_item)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Failed to upsert %s: %s", record.get("link"), exc)

    return {"message": "scrape completed", "inserted": len(inserted)}


@router.get("/search-exa")
def search_exa(max_results: int = 10, x_only: bool = False):
    active_keywords = [k["keyword"] for k in list_keywords()]
    if not active_keywords:
        return {"items": [], "keywords": []}
    results = search_recent_mentions(active_keywords, max_results=max_results, x_only=x_only)
    return {"items": results, "keywords": active_keywords}


@router.post("/ingest-exa")
def ingest_exa(max_results: int = 10, x_only: bool = False):
    active_keywords = [k["keyword"] for k in list_keywords()]
    if not active_keywords:
        return {"message": "no active keywords"}
    results = search_recent_mentions(active_keywords, max_results=max_results, x_only=x_only)
    inserted = 0
    for item in results:
        title = item.get("title")
        url = item.get("url")
        published = item.get("published")
        try:
            date_value = (
                datetime.fromisoformat(published).date().isoformat()
                if published
                else datetime.utcnow().date().isoformat()
            )
        except Exception:
            date_value = datetime.utcnow().date().isoformat()

        # location extraction
        location = extract_location(title or "")
        if not location:
            location = extract_location_with_llm(title or "", "")

        record = {
            "date": date_value,
            "data_source": "Web Search",
            "headline": title or "",
            "summary": None,
            "image_url": None,
            "link": url,
            "media_type": "web article",
            "media_outlet": infer_outlet_from_link(url) if url else None,
            "media_name": infer_outlet_from_link(url) if url else None,
            "status": "unverified",
            "keywords": active_keywords,
            "engagement": 0,
            "location": location,
        }
        try:
            upsert_mention(record)
            inserted += 1
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to upsert EXA result %s: %s", url, exc)

    return {"message": "exa ingestion completed", "inserted": inserted, "fetched": len(results)}


