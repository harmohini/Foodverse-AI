"""Nutrition analysis API routes supporting text and image inputs."""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import AnalysisHistory, NutritionRecord
from app.services.storage import validate_and_save_image
from app.services.nutrition import analyze_nutrition, analyze_nutrition_image
from app.services.ai_provider import get_provider, AIProviderError
from app.schemas.schemas import NutritionRequest, NutritionResponse
from app.core.logging import get_logger

router = APIRouter(prefix="/api/v1/nutrition", tags=["nutrition"])
logger = get_logger(__name__)


@router.post("/analyze", response_model=NutritionResponse)
async def analyze(
    request: NutritionRequest,
    db: Session = Depends(get_db),
):
    """Analyze nutrition for a given food name and serving size."""
    provider = get_provider()
    try:
        result = await analyze_nutrition(request, provider)
    except (AIProviderError, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Nutrition analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    # Save to nutrition records
    nr = NutritionRecord(
        analysis_id=result.metadata.analysis_id,
        food_name=result.nutrition.food_name,
        serving_size=result.nutrition.serving_size,
        calories=result.nutrition.calories,
        protein_g=result.nutrition.protein_g,
        carbs_g=result.nutrition.carbs_g,
        fat_g=result.nutrition.fat_g,
        fiber_g=result.nutrition.fiber_g,
        sugar_g=result.nutrition.sugar_g,
        sodium_mg=result.nutrition.sodium_mg,
        nutrition_score=result.nutrition.nutrition_score,
        source=result.nutrition.source,
    )
    db.add(nr)

    # Save to history
    record = AnalysisHistory(
        analysis_id=result.metadata.analysis_id,
        input_type="text",
        analysis_type="nutrition",
        food_name=result.nutrition.food_name,
        result_json=result.model_dump_json(),
        provider=result.metadata.provider,
        is_demo=result.metadata.is_demo,
    )
    db.add(record)
    db.commit()
    return result


@router.post("/analyze-image", response_model=NutritionResponse)
async def analyze_image(
    file: UploadFile = File(...),
    serving_size: str = Form("1 serving"),
    db: Session = Depends(get_db),
):
    """Estimate nutrition from an uploaded food image."""
    image_path = await validate_and_save_image(file)
    provider = get_provider()
    try:
        result = await analyze_nutrition_image(str(image_path), serving_size, provider)
    except (AIProviderError, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Nutrition image analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    # Save to nutrition records
    nr = NutritionRecord(
        analysis_id=result.metadata.analysis_id,
        food_name=result.nutrition.food_name,
        serving_size=result.nutrition.serving_size,
        calories=result.nutrition.calories,
        protein_g=result.nutrition.protein_g,
        carbs_g=result.nutrition.carbs_g,
        fat_g=result.nutrition.fat_g,
        fiber_g=result.nutrition.fiber_g,
        sugar_g=result.nutrition.sugar_g,
        sodium_mg=result.nutrition.sodium_mg,
        nutrition_score=result.nutrition.nutrition_score,
        source=result.nutrition.source,
    )
    db.add(nr)

    # Save to history
    record = AnalysisHistory(
        analysis_id=result.metadata.analysis_id,
        input_type="image",
        analysis_type="nutrition",
        food_name=result.nutrition.food_name,
        result_json=result.model_dump_json(),
        provider=result.metadata.provider,
        is_demo=result.metadata.is_demo,
        file_path=str(image_path),
    )
    db.add(record)
    db.commit()
    return result
