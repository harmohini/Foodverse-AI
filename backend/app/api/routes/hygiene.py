"""Restaurant hygiene monitoring routes."""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import AnalysisHistory
from app.services.storage import validate_and_save_video
from app.services.hygiene import analyze_hygiene
from app.services.ai_provider import get_provider
from app.schemas.schemas import HygieneReport
from app.core.logging import get_logger

router = APIRouter(prefix="/api/v1/hygiene", tags=["hygiene"])
logger = get_logger(__name__)


@router.post("/analyze", response_model=HygieneReport)
async def analyze(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a video and analyze restaurant hygiene indicators."""
    video_path = await validate_and_save_video(file)
    provider = get_provider()
    try:
        result = await analyze_hygiene(str(video_path), provider)
    except Exception as e:
        logger.error(f"Hygiene analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    record = AnalysisHistory(
        analysis_id=result.metadata.analysis_id,
        input_type="video",
        analysis_type="hygiene",
        food_name="Restaurant hygiene check",
        result_json=result.model_dump_json(),
        provider=result.metadata.provider,
        is_demo=result.metadata.is_demo,
        file_path=str(video_path),
    )
    db.add(record)
    db.commit()
    return result
