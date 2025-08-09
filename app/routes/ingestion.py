from fastapi import APIRouter, HTTPException
from app.db.supabase_client import upsert_health_mention
from app.models.schemas import SocialMediaIngest


router = APIRouter(tags=["ingestion"])


@router.post("/ingest-social-media")
def ingest_social_media(payload: SocialMediaIngest):
    try:
        record = {
            "date": payload.date.isoformat(),
            "data_source": "Social Media",
            "headline": payload.headline,
            "summary": payload.summary,
            "image_url": str(payload.image_url) if payload.image_url else None,
            "link": str(payload.link),
            "media_type": "social media",
            "media_outlet": payload.media_name or "Social",
            "media_name": payload.media_name or "Social",
            "status": "unverified",
            "keywords": payload.keywords or [],
            "engagement": payload.engagement or 0,
        }
        return upsert_health_mention(record)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


