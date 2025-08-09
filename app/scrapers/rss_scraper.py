from __future__ import annotations

from typing import Dict, List, Optional
from datetime import datetime
import time
import feedparser


OUTLET_BY_HOST = {
    "www.thestar.com.my": "The Star",
    "www.malaymail.com": "Malay Mail",
}


def infer_outlet_from_link(link: str) -> Optional[str]:
    try:
        # Lazy hostname extraction
        host = link.split("//", 1)[1].split("/", 1)[0]
        return OUTLET_BY_HOST.get(host)
    except Exception:  # noqa: BLE001
        return None


def fetch_rss_entries(feed_url: str) -> List[Dict[str, str]]:
    parsed = feedparser.parse(feed_url)
    results: List[Dict[str, str]] = []
    for entry in parsed.entries:
        title = getattr(entry, "title", None)
        summary = getattr(entry, "summary", None) or getattr(entry, "description", None)
        link = getattr(entry, "link", None)
        # Prefer structured parsed dates to derive ISO date
        published_date = None
        try:
            if hasattr(entry, "published_parsed") and getattr(entry, "published_parsed"):
                dt = datetime.fromtimestamp(time.mktime(getattr(entry, "published_parsed")))
                published_date = dt.date().isoformat()
            elif hasattr(entry, "updated_parsed") and getattr(entry, "updated_parsed"):
                dt = datetime.fromtimestamp(time.mktime(getattr(entry, "updated_parsed")))
                published_date = dt.date().isoformat()
        except Exception:
            published_date = None

        outlet = infer_outlet_from_link(link) if link else None
        # image: check common RSS media fields
        image_url = None
        try:
            if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                image_url = entry.media_thumbnail[0].get("url")
            elif hasattr(entry, "media_content") and entry.media_content:
                image_url = entry.media_content[0].get("url")
        except Exception:
            image_url = None
        results.append(
            {
                "title": title,
                "summary": summary,
                "link": link,
                "published_date": published_date,
                "outlet": outlet,
                "image_url": image_url,
            }
        )
    return results


