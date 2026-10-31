"""Restaurant hygiene monitoring routes supporting media uploads and text descriptions."""
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import AnalysisHistory
from app.services.storage import validate_and_save_media
from app.services.hygiene import analyze_hygiene, analyze_hygiene_text
from app.services.ai_provider import get_provider, AIProviderError
from app.schemas.schemas import HygieneReport, HygieneTextRequest
from app.core.logging import get_logger

router = APIRouter(prefix="/api/v1/hygiene", tags=["hygiene"])
logger = get_logger(__name__)


@router.post("/analyze", response_model=HygieneReport)
async def analyze(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Analyze restaurant hygiene indicators from an uploaded image/video or text description."""
    if not file and not text:
        raise HTTPException(
            status_code=422,
            detail="Either an image/video file or text description must be provided.",
        )

    provider = get_provider()
    media_path = None
    input_type = "video"

    try:
        if file is not None and getattr(file, "filename", None):
            media_path, media_type = await validate_and_save_media(file)
            input_type = media_type
            result = await analyze_hygiene(str(media_path), provider, media_type=media_type)
        elif text:
            input_type = "text"
            result = await analyze_hygiene_text(text.strip(), provider)
        else:
            raise HTTPException(
                status_code=422,
                detail="Either an image/video file or text description must be provided.",
            )
    except (AIProviderError, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Hygiene analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    record = AnalysisHistory(
        analysis_id=result.metadata.analysis_id,
        input_type=input_type,
        analysis_type="hygiene",
        food_name="Restaurant hygiene check",
        result_json=result.model_dump_json(),
        provider=result.metadata.provider,
        is_demo=result.metadata.is_demo,
        file_path=str(media_path) if media_path else None,
    )
    db.add(record)
    db.commit()
    return result


@router.post("/analyze-text", response_model=HygieneReport)
async def analyze_text_route(
    payload: HygieneTextRequest,
    db: Session = Depends(get_db),
):
    """Analyze restaurant hygiene indicators from a JSON text description."""
    provider = get_provider()
    try:
        result = await analyze_hygiene_text(payload.text.strip(), provider)
    except (AIProviderError, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Hygiene text analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    record = AnalysisHistory(
        analysis_id=result.metadata.analysis_id,
        input_type="text",
        analysis_type="hygiene",
        food_name="Restaurant hygiene check",
        result_json=result.model_dump_json(),
        provider=result.metadata.provider,
        is_demo=result.metadata.is_demo,
    )
    db.add(record)
    db.commit()
    return result
