"""Freshness analysis routes supporting image and text inputs."""
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import AnalysisHistory
from app.services.storage import validate_and_save_image
from app.services.freshness import analyze_freshness, analyze_freshness_text
from app.services.ai_provider import get_provider, AIProviderError
from app.schemas.schemas import FreshnessResult, FreshnessTextRequest
from app.core.logging import get_logger

router = APIRouter(prefix="/api/v1/freshness", tags=["freshness"])
logger = get_logger(__name__)


@router.post("/analyze", response_model=FreshnessResult)
async def analyze(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    food_category: str = Form(default=""),
    db: Session = Depends(get_db),
):
    """Assess food freshness from an image upload or text description."""
    if not file and not text:
        raise HTTPException(
            status_code=422,
            detail="Either an image file or text description must be provided.",
        )

    provider = get_provider()
    image_path = None
    input_type = "image"

    try:
        if file is not None and getattr(file, "filename", None):
            image_path = await validate_and_save_image(file)
            result = await analyze_freshness(str(image_path), food_category, provider)
        elif text:
            input_type = "text"
            result = await analyze_freshness_text(text.strip(), food_category, provider)
        else:
            raise HTTPException(
                status_code=422,
                detail="Either an image file or text description must be provided.",
            )
    except (AIProviderError, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Freshness analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    record = AnalysisHistory(
        analysis_id=result.metadata.analysis_id,
        input_type=input_type,
        analysis_type="freshness",
        food_name=food_category or "Unknown",
        result_json=result.model_dump_json(),
        provider=result.metadata.provider,
        is_demo=result.metadata.is_demo,
        file_path=str(image_path) if image_path else None,
    )
    db.add(record)
    db.commit()
    return result


@router.post("/analyze-text", response_model=FreshnessResult)
async def analyze_text_route(
    payload: FreshnessTextRequest,
    db: Session = Depends(get_db),
):
    """Assess food freshness from a JSON text description."""
    provider = get_provider()
    try:
        result = await analyze_freshness_text(payload.text.strip(), payload.food_category, provider)
    except (AIProviderError, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Freshness text analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    record = AnalysisHistory(
        analysis_id=result.metadata.analysis_id,
        input_type="text",
        analysis_type="freshness",
        food_name=payload.food_category or "Unknown",
        result_json=result.model_dump_json(),
        provider=result.metadata.provider,
        is_demo=result.metadata.is_demo,
    )
    db.add(record)
    db.commit()
    return result
