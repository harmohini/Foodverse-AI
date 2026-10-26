"""Food recognition API routes."""
import json
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import AnalysisHistory
from app.services.storage import validate_and_save_image
from app.services.food_recognition import recognize_food
from app.services.ai_provider import get_provider
from app.schemas.schemas import FoodRecognitionResult
from app.core.logging import get_logger

router = APIRouter(prefix="/api/v1/food", tags=["food"])
logger = get_logger(__name__)


@router.post("/recognize", response_model=FoodRecognitionResult)
async def recognize(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload an image and identify the food."""
    image_path = await validate_and_save_image(file)
    provider = get_provider()

    try:
        result = await recognize_food(str(image_path), provider)
    except Exception as e:
        logger.error(f"Food recognition error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    # Persist to history
    record = AnalysisHistory(
        analysis_id=result.metadata.analysis_id,
        input_type="image",
        analysis_type="food_recognition",
        food_name=result.dish_name,
        result_json=result.model_dump_json(),
        provider=result.metadata.provider,
        is_demo=result.metadata.is_demo,
        file_path=str(image_path),
    )
    db.add(record)
    db.commit()
    return result
