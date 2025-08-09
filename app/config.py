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
        "https://www.malaysiakini.com/rss/en/news.rss",
        "https://bernama.com/en/rssfeed.php",
        "https://www.lowyat.net/feed/"
        "https://news.google.com/rss?hl=en-MY&gl=MY&ceid=MY:en",
        "https://news.google.com/rss?hl=ms-MY&gl=MY&ceid=MY:ms",
        "https://news.google.com/rss/search?q=Malaysia&hl=en-MY&gl=MY&ceid=MY:en",
        "https://malaysiakini.com/feeds/en/news.xml",
        "http://www.themalaysianinsider.com/rss",
        "http://mmail.com.my/rss2",
        "http://freemalaysiatoday.com/feed",
        "https://www.malaymail.com/rss",
        "https://bernama.com/en/rssfeed.php",
        "https://lowyat.net/feed",
        "https://paultan.org/feed",
        "https://says.com/my/rss",
        "https://kosmo.com.my/cmlink/popular-1.554376",
        "https://theborneopost.com/feed",
        "https://malaysia-today.net/feed",
        "https://sarawakreport.org/feed",
        "https://heraldmalaysia.com/home/rss",
        "https://christianitymalaysia.com/wp/feed/",
        "https://feeds.malaysianews.net/rss/48cba686fe041718",
        "https://thestar.com.my/rss/",
        "http://www.nst.com.my/nst/RSS/index_html",
        "http://www.hmetro.com.my/rss/",
        "https://thesundaily.my/rss",
        "https://thesun.my/rss/home",
        "https://thesun.my/rss/local",
        "https://thesun.my/rss/viral",
        "https://thesun.my/rss/viral/going-viral",
        "https://thesun.my/rss/viral/sedang-viral",
        "https://thesun.my/rss/world",
        "https://thesun.my/rss/business",
        "https://thesun.my/rss/sport",
        "https://thesun.my/rss/style-life",
        "https://thesun.my/rss/spotlight",
        "https://thesun.my/rss/opinion",
        "https://thesun.my/rss/gear-up",
        "https://thesun.my/rss/berita",
        "https://thesun.my/rss/images",
        "https://thesun.my/rss/education"
    ]
    # Malaysia location dictionary (basic) for extraction
    malaysia_states: list[str] = [
        "Johor", "Kedah", "Kelantan", "Melaka", "Negeri Sembilan", "Pahang",
        "Penang", "Pulau Pinang", "Perak", "Perlis", "Sabah", "Sarawak",
        "Selangor", "Terengganu", "Kuala Lumpur", "Labuan", "Putrajaya",
    ]

    # OpenRouter (OpenAI-compatible) LLM settings
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openai/gpt-4o-mini"
    enable_llm_location: bool = True

    # Exa Search
    exa_api_key: str | None = None



def get_settings() -> Settings:
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    return Settings(
        supabase_url=url,
        supabase_service_role_key=key,
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        openrouter_model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        enable_llm_location=os.getenv("ENABLE_LLM_LOCATION", "true").lower() in {"1", "true", "yes"},
        exa_api_key=os.getenv("EXA_API_KEY"),
    )


