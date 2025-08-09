import os
from pydantic import BaseModel


class Settings(BaseModel):
    supabase_url: str
    supabase_service_role_key: str

    # Scraper configuration
    rss_feeds: list[str] = [
        # The Star - general news RSS (example)
        "https://www.thestar.com.my/rss/News/Nation",
        # Malay Mail - Malaysia RSS (example)
        "https://www.malaymail.com/feed/rss/malaysia",
    ]


def get_settings() -> Settings:
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    return Settings(supabase_url=url, supabase_service_role_key=key)


