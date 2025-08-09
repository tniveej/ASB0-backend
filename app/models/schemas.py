from datetime import date
from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field


class KeywordCreate(BaseModel):
    keyword: str = Field(min_length=2)


class Keyword(BaseModel):
    id: str
    keyword: str
    is_active: bool


class SocialMediaIngest(BaseModel):
    date: date
    headline: Optional[str] = None
    summary: Optional[str] = None
    image_url: Optional[HttpUrl] = None
    link: HttpUrl
    media_name: Optional[str] = None
    keywords: Optional[List[str]] = None
    engagement: Optional[int] = 0


class HealthMention(BaseModel):
    id: str
    date: date
    data_source: str
    headline: Optional[str]
    summary: Optional[str]
    image_url: Optional[str]
    link: str
    media_type: Optional[str]
    media_outlet: Optional[str]
    media_name: Optional[str]
    status: Optional[str]
    keywords: Optional[List[str]]
    engagement: Optional[int]


class MentionFilters(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    data_source: Optional[str] = None
    status: Optional[str] = None
    keywords: Optional[List[str]] = None
    page: int = 1
    page_size: int = 20


class StatusUpdate(BaseModel):
    status: str


