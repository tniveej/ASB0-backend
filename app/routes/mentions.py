from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.db.supabase_client import (
    list_mentions,
    update_mention_status,
)
from app.models.schemas import StatusUpdate
from app.services.postprocess_locations import postprocess_locations
from app.services.cleanup_service import clean_mentions_with_llm

router = APIRouter(prefix="/health-mentions", tags=["health-mentions"])


@router.get("")
def get_health_mentions(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_source: Optional[str] = None,
    status: Optional[str] = None,
    keywords: Optional[str] = Query(
        default=None, description="Comma-separated keyword list"
    ),
    page: int = 1,
    page_size: int = 20,
):
    keyword_list = (
        [k.strip() for k in keywords.split(",") if k.strip()] if keywords else None
    )
    items, total = list_mentions(
        start_date=start_date,
        end_date=end_date,
        data_source=data_source,
        status=status,
        keywords=keyword_list,
        page=page,
        page_size=page_size,
    )
    return {"items": items, "page": page, "page_size": page_size, "total": total}


@router.put("/{mention_id}/status")
def put_health_mention_status(mention_id: str, payload: StatusUpdate):
    try:
        return update_mention_status(mention_id, payload.status)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/postprocess-locations")
def run_postprocess_locations(limit: int = 50):
    try:
        result = postprocess_locations(limit=limit)
        return result
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/clean-metadata")
def run_clean_metadata(limit: int = 50):
    try:
        result = clean_mentions_with_llm(limit=limit)
        return result
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


