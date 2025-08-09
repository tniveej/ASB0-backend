from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.db.supabase_client import (
    add_keyword_manager,
    list_keywords,
    find_keyword,
    disable_keyword,
    delete_keyword,
)
from app.models.schemas import KeywordCreate


router = APIRouter(prefix="/keywords", tags=["keywords"])


@router.post("")
def create_keyword(payload: KeywordCreate):
    try:
        # enforce uniqueness (case-insensitive)
        exists = find_keyword(payload.keyword.strip())
        if exists and exists.get("enabled", True):
            raise HTTPException(status_code=409, detail="Keyword already exists")
        now = datetime.utcnow().replace(microsecond=0)
        entry = {
            "keyword": payload.keyword.strip(),
            "threshold": 0,
            "current": 0,
            "status": None,
            "district": None,
            "timestamp": now.isoformat(),
            "priority": None,
            "enabled": True,
        }
        return add_keyword_manager(entry)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("")
def get_keywords():
    return list_keywords()


@router.delete("/{keyword_id}")
def remove_keyword(keyword_id: str, hard_delete: bool = False):
    try:
        if hard_delete:
            return delete_keyword(keyword_id)
        return disable_keyword(keyword_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


