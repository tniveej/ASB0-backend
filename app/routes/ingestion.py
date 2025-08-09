from fastapi import APIRouter, HTTPException
from app.db.supabase_client import upsert_mention
from app.models.schemas import SocialMediaIngest
from app.scrapers.location_extractor import extract_location


router = APIRouter(tags=["ingestion"])


@router.post("/ingest-social-media")
def ingest_social_media(payload: SocialMediaIngest):
    try:
        # Try extract location from headline + summary + optional hint
        location_text = " ".join(
            filter(
                None,
                [payload.headline or "", payload.summary or "", payload.location_hint or ""],
            )
        )
        location = extract_location(location_text)

        record = {
            "date": payload.date.isoformat(),
            "data_source": "Social Media",
            "headline": payload.headline or "",
            "summary": payload.summary,
            "image_url": str(payload.image_url) if payload.image_url else None,
            "link": str(payload.link),
            "media_type": "social media",
            "media_outlet": payload.media_name or "Social",
            "media_name": payload.media_name or "Social",
            "status": "unverified",
            "keywords": payload.keywords or [],
            "engagement": payload.engagement or 0,
            "location": location,
        }
        return upsert_mention(record)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


