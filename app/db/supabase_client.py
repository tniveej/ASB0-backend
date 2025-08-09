from typing import Any, Dict, List, Optional, Tuple
import logging
from supabase import create_client, Client

from app.config import get_settings


logger = logging.getLogger(__name__)

_supabase_client: Optional[Client] = None


def get_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise RuntimeError("Supabase URL or Service Role Key not configured")
        _supabase_client = create_client(
            settings.supabase_url, settings.supabase_service_role_key
        )
        logger.info("Initialized Supabase client")
    return _supabase_client


def upsert_mention(data: Dict[str, Any]) -> Dict[str, Any]:
    """Insert into mentions if no existing row with the same link. Return the row."""
    client = get_client()
    link = data.get("link")
    if link:
        existing = (
            client.table("mentions").select("*").eq("link", link).limit(1).execute()
        )
        if existing.data:
            return existing.data[0]
    resp = client.table("mentions").insert(data).execute()
    if not resp.data:
        raise RuntimeError("Insert failed")
    return resp.data[0]


def list_mentions(
    *,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_source: Optional[str] = None,
    status: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[Dict[str, Any]], int]:
    client = get_client()
    query = client.table("mentions").select("*")

    if start_date:
        query = query.gte("date", start_date)
    if end_date:
        query = query.lte("date", end_date)
    if data_source:
        query = query.eq("data_source", data_source)
    if status:
        query = query.eq("status", status)
    if keywords:
        # Array overlap - PostgREST uses 'ov' for overlap
        query = query.overlaps("keywords", keywords)

    range_from = (page - 1) * page_size
    range_to = range_from + page_size - 1
    query = query.range(range_from, range_to)

    resp = query.execute()
    if resp.data is None:
        return [], 0

    # Get total count with a separate call due to range applied
    count_query = client.table("mentions").select("id", count="exact")
    if start_date:
        count_query = count_query.gte("date", start_date)
    if end_date:
        count_query = count_query.lte("date", end_date)
    if data_source:
        count_query = count_query.eq("data_source", data_source)
    if status:
        count_query = count_query.eq("status", status)
    if keywords:
        count_query = count_query.overlaps("keywords", keywords)
    count_resp = count_query.execute()
    total = count_resp.count or 0

    return resp.data, total


def update_mention_status(mention_id: str, status: str) -> Dict[str, Any]:
    client = get_client()
    resp = client.table("mentions").update({"status": status}).eq("id", mention_id).execute()
    if not resp.data:
        raise RuntimeError("Mention not found or update failed")
    return resp.data[0]


def add_keyword_manager(entry: Dict[str, Any]) -> Dict[str, Any]:
    client = get_client()
    resp = client.table("keyword_manager").insert(entry).execute()
    if not resp.data:
        raise RuntimeError("Keyword insert failed")
    return resp.data[0]


def list_keywords() -> List[Dict[str, Any]]:
    client = get_client()
    resp = client.table("keyword_manager").select("*").eq("enabled", True).execute()
    return resp.data or []


def find_keyword(keyword: str) -> Optional[Dict[str, Any]]:
    """Find keyword case-insensitively in keyword_manager."""
    client = get_client()
    resp = (
        client.table("keyword_manager")
        .select("*")
        .ilike("keyword", keyword)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None


def disable_keyword(keyword_id: str) -> Dict[str, Any]:
    client = get_client()
    resp = (
        client.table("keyword_manager").update({"enabled": False}).eq("id", keyword_id).execute()
    )
    if not resp.data:
        raise RuntimeError("Keyword not found or update failed")
    return resp.data[0]


def delete_keyword(keyword_id: str) -> Dict[str, Any]:
    client = get_client()
    resp = client.table("keyword_manager").delete().eq("id", keyword_id).execute()
    # Some PostgREST setups may not return deleted rows; return minimal info
    return resp.data[0] if resp.data else {"id": keyword_id, "deleted": True}


