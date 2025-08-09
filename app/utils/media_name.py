from __future__ import annotations

from urllib.parse import urlparse


HOST_TO_NAME = {
    "www.thestar.com.my": "The Star",
    "thestar.com.my": "The Star",
    "www.malaymail.com": "Malay Mail",
    "malaymail.com": "Malay Mail",
    "www.nst.com.my": "New Straits Times",
    "nst.com.my": "New Straits Times",
    "www.bernama.com": "Bernama",
    "bernama.com": "Bernama",
    "www.freemalaysiatoday.com": "Free Malaysia Today",
    "freemalaysiatoday.com": "Free Malaysia Today",
    "www.theedgemalaysia.com": "The Edge Malaysia",
    "theedgemalaysia.com": "The Edge Malaysia",
    "www.theborneopost.com": "The Borneo Post",
    "theborneopost.com": "The Borneo Post",
    "www.dailyexpress.com.my": "Daily Express",
    "dailyexpress.com.my": "Daily Express",
    "www.malaysiakini.com": "Malaysiakini",
    "malaysiakini.com": "Malaysiakini",
    "www.straitstimes.com": "The Straits Times",
    "straitstimes.com": "The Straits Times",
    "x.com": "X",
    "twitter.com": "X",
    "mobile.twitter.com": "X",
    "www.twitter.com": "X",
    "reddit.com": "Reddit",
    "www.reddit.com": "Reddit",
    "youtube.com": "YouTube",
    "www.youtube.com": "YouTube",
}


def infer_media_name_from_url(url: str | None) -> str | None:
    if not url:
        return None
    try:
        host = urlparse(url).netloc.lower()
        if host in HOST_TO_NAME:
            return HOST_TO_NAME[host]
        # Fallback: use second-level domain as title case
        parts = host.split(".")
        if len(parts) >= 2:
            base = parts[-2]
            return base.replace("-", " ").title()
        return host
    except Exception:
        return None


