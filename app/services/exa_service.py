from __future__ import annotations

from typing import List, Dict, Any
from exa_py import Exa

from app.config import get_settings
from datetime import datetime, timedelta, timezone
from app.utils.keyword_match import choose_best_keyword
from app.utils.media_name import infer_media_name_from_url
from app.location.locations import normalize_location
from app.llm.location_llm import extract_location_with_llm


def get_exa_client() -> Exa:
    settings = get_settings()
    if not settings.exa_api_key:
        raise RuntimeError("EXA_API_KEY is not set")
    return Exa(api_key=settings.exa_api_key)


def _get_attr(obj: Any, *names: str) -> Any:
    for n in names:
        if hasattr(obj, n):
            return getattr(obj, n)
        if isinstance(obj, dict) and n in obj:
            return obj[n]
    return None


def search_recent_mentions(
    keywords: List[str],
    max_results: int = 10,
    include_social: bool = True,
) -> List[Dict]:
    """Search Exa for recent Malaysian mentions of provided keywords.
    Restrict to recent content and preferred domains (news + social).
    """
    exa = get_exa_client()
    if not keywords:
        return []
    settings = get_settings()
    # Natural language query focusing strictly on Malaysia, biasing towards .my outlets
    kw_expr = " OR ".join(f'"{k}"' for k in keywords)
    outlet_bias = (
        "The Star, Malay Mail, NST, Bernama, Malaysiakini, Free Malaysia Today, The Edge Malaysia, "
        "The Borneo Post, Daily Express, Utusan, Harian Metro, Kosmo"
    )
    query = (
        f"health-related news or social media posts in Malaysia about ({kw_expr}). "
        f"Prefer Malaysian sources, .my domains, and local outlets such as {outlet_bias}."
    )

    # Date filter: constrain to the current year (inclusive)
    now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
    year_start = datetime(now_utc.year, 1, 1, tzinfo=timezone.utc)
    # Exa expects ISO 8601; ensure trailing 'Z'
    start_date = year_start.isoformat().replace("+00:00", "Z")
    end_date = now_utc.isoformat().replace("+00:00", "Z")

    # Use excludeDomains to drop known irrelevant domains (e.g., Wikipedia/YouTube)
    exclude_domains = list({*settings.exa_exclude_domains})

    # Pass excludeDomains only (cannot combine with includeDomains). Also bound by current-year window.
    resp = exa.search(
        query=query,
        num_results=max_results,
        start_published_date=start_date,
        end_published_date=end_date,
        exclude_domains=exclude_domains,
        use_autoprompt=True,
    )
    # Exa returns a SearchResponse with a `.results` list
    raw_results = _get_attr(resp, "results") or []
    # If SDK version returns dict, handle that too
    if isinstance(resp, dict):
        raw_results = resp.get("results", [])

    items: List[Dict] = []
    for r in raw_results:
        items.append(
            {
                "title": _get_attr(r, "title"),
                "url": _get_attr(r, "url"),
                "score": _get_attr(r, "score"),
                "published": _get_attr(
                    r,
                    "published",
                    "published_date",
                    "publishedDate",
                    "date",
                ),
            }
        )
    return items


def enrich_with_exa_contents(records: List[Dict]) -> List[Dict]:
    """Given list of results with 'url' keys, fetch content via Exa get_contents and
    produce enriched mention dicts including a summary and best keyword/media/location.
    """
    settings = get_settings()
    exa = get_exa_client()
    urls = [r.get("url") for r in records if r.get("url")]
    if not urls:
        return []
    try:
        contents = exa.get_contents(urls=urls)
    except Exception:
        contents = None
    raw_items = []
    if isinstance(contents, dict):
        raw_items = contents.get("results", [])
    else:
        raw_items = getattr(contents, "results", []) or []

    url_to_text: Dict[str, str] = {}
    url_to_summary: Dict[str, str] = {}
    for item in raw_items:
        url = item.get("url") if isinstance(item, dict) else getattr(item, "url", None)
        summary = item.get("summary") if isinstance(item, dict) else getattr(item, "summary", None)
        text = item.get("text") if isinstance(item, dict) else getattr(item, "text", None)
        if url:
            if text:
                url_to_text[url] = text
            if summary:
                url_to_summary[url] = summary

    allowed_keywords = [k["keyword"] for k in __import__("app.db.supabase_client", fromlist=["list_keywords"]).list_keywords()]  # lazy import to avoid cycle

    enriched: List[Dict] = []
    for r in records:
        url = r.get("url")
        text = url_to_text.get(url, "")
        summary = url_to_summary.get(url) or r.get("title")
        # best keyword
        best_kw = choose_best_keyword(" ".join([r.get("title") or "", text]), allowed_keywords)
        # media name
        media_name = infer_media_name_from_url(url) or r.get("source") or "Unknown"
        # location via rules -> LLM fallback on text
        loc = extract_location_with_llm(r.get("title") or "", text or "")

        enriched.append(
            {
                "headline": r.get("title") or "",
                "summary": summary or "",
                "link": url,
                "media_name": media_name,
                "keywords": [best_kw],
                "location": loc or None,
            }
        )
    return enriched


