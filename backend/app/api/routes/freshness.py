"""Freshness analysis routes."""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import AnalysisHistory
from app.services.storage import validate_and_save_image
from app.services.freshness import analyze_freshness
from app.services.ai_provider import get_provider
from app.schemas.schemas import FreshnessResult
from app.core.logging import get_logger

router = APIRouter(prefix="/api/v1/freshness", tags=["freshness"])
logger = get_logger(__name__)


@router.post("/analyze", response_model=FreshnessResult)
async def analyze(
    file: UploadFile = File(...),
    food_category: str = Form(default=""),
    db: Session = Depends(get_db),
):
    """Upload a food image and assess its freshness."""
    image_path = await validate_and_save_image(file)
    provider = get_provider()
    try:
        result = await analyze_freshness(str(image_path), food_category, provider)
    except Exception as e:
        logger.error(f"Freshness analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    record = AnalysisHistory(
        analysis_id=result.metadata.analysis_id,
        input_type="image",
        analysis_type="freshness",
        food_name=food_category or "Unknown",
        result_json=result.model_dump_json(),
        provider=result.metadata.provider,
        is_demo=result.metadata.is_demo,
        file_path=str(image_path),
    )
    db.add(record)
    db.commit()
    return result
