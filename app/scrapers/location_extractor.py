from __future__ import annotations

from typing import Dict, Optional
import re

from app.config import get_settings


_KNOWN_DISTRICTS = [
    # Common Klang Valley municipalities/districts; extend as needed
    "Petaling Jaya", "Shah Alam", "Subang Jaya", "Klang", "Gombak", "Hulu Langat",
    "Hulu Selangor", "Sepang", "Sabak Bernam", "Kuala Langat",
    "George Town", "Butterworth", "Seberang Perai",
    "Ipoh", "Johor Bahru", "Kota Kinabalu", "Kuching", "Miri", "Sandakan",
    "Alor Setar", "Kuantan", "Seremban", "Melaka", "Kangar", "Kuala Terengganu",
]


def extract_location(text: str) -> Optional[Dict[str, str]]:
    """Very lightweight extractor that looks for states and known districts.
    Returns a dict like {"state": ..., "district": ..., "match": ...} or None.
    """
    if not text:
        return None

    settings = get_settings()
    lowered = text.lower()

    # State detection
    state_match = None
    for state in settings.malaysia_states:
        if state.lower() in lowered:
            state_match = state
            break

    # District detection (simple exact substring)
    district_match = None
    for district in _KNOWN_DISTRICTS:
        # word-boundary-ish match to reduce false positives
        pattern = r"\b" + re.escape(district) + r"\b"
        if re.search(pattern, text, flags=re.IGNORECASE):
            district_match = district
            break

    if state_match or district_match:
        result: Dict[str, str] = {}
        if state_match:
            result["state"] = state_match
        if district_match:
            result["district"] = district_match
        return result

    return None


