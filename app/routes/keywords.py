from fastapi import APIRouter, HTTPException
from app.db.supabase_client import add_keyword, list_keywords
from app.models.schemas import KeywordCreate


router = APIRouter(prefix="/keywords", tags=["keywords"])


@router.post("")
def create_keyword(payload: KeywordCreate):
    try:
        return add_keyword(payload.keyword.strip())
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("")
def get_keywords():
    return list_keywords()


