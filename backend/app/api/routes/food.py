"""Food recognition API routes supporting image and text inputs."""
import json
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import AnalysisHistory
from app.services.storage import validate_and_save_image
from app.services.food_recognition import recognize_food, recognize_food_text
from app.services.ai_provider import get_provider, AIProviderError
from app.schemas.schemas import FoodRecognitionResult, FoodRecognitionTextRequest
from app.core.logging import get_logger

router = APIRouter(prefix="/api/v1/food", tags=["food"])
logger = get_logger(__name__)


@router.post("/recognize", response_model=FoodRecognitionResult)
async def recognize(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Identify food from an image upload or text description."""
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
            result = await recognize_food(str(image_path), provider)
        elif text:
            input_type = "text"
            result = await recognize_food_text(text.strip(), provider)
        else:
            raise HTTPException(
                status_code=422,
                detail="Either an image file or text description must be provided.",
            )
    except (AIProviderError, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Food recognition error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    # Persist to history
    record = AnalysisHistory(
        analysis_id=result.metadata.analysis_id,
        input_type=input_type,
        analysis_type="food_recognition",
        food_name=result.dish_name,
        result_json=result.model_dump_json(),
        provider=result.metadata.provider,
        is_demo=result.metadata.is_demo,
        file_path=str(image_path) if image_path else None,
    )
    db.add(record)
    db.commit()
    return result


@router.post("/recognize-text", response_model=FoodRecognitionResult)
async def recognize_from_text(
    payload: FoodRecognitionTextRequest,
    db: Session = Depends(get_db),
):
    """Identify food from a JSON text description."""
    provider = get_provider()
    try:
        result = await recognize_food_text(payload.text.strip(), provider)
    except (AIProviderError, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Food recognition from text error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    record = AnalysisHistory(
        analysis_id=result.metadata.analysis_id,
        input_type="text",
        analysis_type="food_recognition",
        food_name=result.dish_name,
        result_json=result.model_dump_json(),
        provider=result.metadata.provider,
        is_demo=result.metadata.is_demo,
    )
    db.add(record)
    db.commit()
    return result
