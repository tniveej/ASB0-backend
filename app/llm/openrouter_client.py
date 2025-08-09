from typing import Optional
from openai import OpenAI

from app.config import get_settings


_client: Optional[OpenAI] = None


def get_openrouter_client() -> OpenAI:
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.openrouter_api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set")
        _client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )
    return _client


