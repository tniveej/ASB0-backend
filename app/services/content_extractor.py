from __future__ import annotations

from typing import Optional
import logging

import trafilatura

from app.config import get_settings
from app.services.exa_service import get_exa_client


logger = logging.getLogger(__name__)


def extract_main_text(url: str) -> Optional[str]:
    """Extract main article text from a URL using trafilatura.
    Fallback to Exa content extraction when available.
    """
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=False,
            )
            if text and text.strip():
                return text.strip()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Trafilatura failed for %s: %s", url, exc)

    # Fallback via Exa if configured
    try:
        settings = get_settings()
        if settings.exa_api_key:
            exa = get_exa_client()
            # Some SDKs support urls parameter; wrap in try/except
            try:
                contents = exa.get_contents(urls=[url])
                # Normalize
                items = contents.get("results", []) if isinstance(contents, dict) else getattr(contents, "results", [])
                for item in items:
                    # Try different fields for text
                    text = (
                        getattr(item, "text", None)
                        or getattr(item, "content", None)
                        or (item.get("text") if isinstance(item, dict) else None)
                        or (item.get("content") if isinstance(item, dict) else None)
                    )
                    if text and text.strip():
                        return text.strip()
            except Exception as exa_exc:  # noqa: BLE001
                logger.info("Exa get_contents not available/failed for %s: %s", url, exa_exc)
    except Exception:
        # No exa client or not configured
        pass

    return None


