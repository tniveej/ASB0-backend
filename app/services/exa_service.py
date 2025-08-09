from __future__ import annotations

from typing import List, Dict, Any
from exa_py import Exa

from app.config import get_settings


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


def search_recent_mentions(keywords: List[str], max_results: int = 10) -> List[Dict]:
    """Search Exa for recent Malaysian mentions of provided keywords.
    Uses a simple OR query across keywords and biases to Malaysia by including country term.
    """
    exa = get_exa_client()
    if not keywords:
        return []
    query = " OR ".join(keywords) + " Malaysia"
    # Basic recent search; Exa supports advanced params; keep minimal here
    resp = exa.search(query=query, num_results=max_results)
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


