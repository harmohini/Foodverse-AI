"""Smart cooking assistant routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import AnalysisHistory, RecipeRecord
from app.services.cooking import generate_recipe, chat_about_recipe
from app.services.ai_provider import get_provider, AIProviderError
from app.schemas.schemas import CookingRequest, CookingChatRequest, Recipe, CookingChatResponse
from app.core.logging import get_logger

router = APIRouter(prefix="/api/v1/cooking", tags=["cooking"])
logger = get_logger(__name__)


@router.post("/generate", response_model=Recipe)
async def generate(
    request: CookingRequest,
    db: Session = Depends(get_db),
):
    """Generate a recipe based on the given parameters."""
    provider = get_provider()
    try:
        recipe = await generate_recipe(request, provider)
    except (AIProviderError, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Recipe generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Recipe generation failed: {e}")

    # Save recipe record
    rr = RecipeRecord(
        recipe_id=recipe.recipe_id,
        title=recipe.title,
        cuisine=recipe.cuisine,
        dietary_pref=recipe.dietary_info,
        difficulty=recipe.difficulty,
        servings=recipe.servings,
        recipe_json=recipe.model_dump_json(),
        is_demo=recipe.is_demo,
    )
    db.add(rr)

    # History
    record = AnalysisHistory(
        analysis_id=recipe.recipe_id,
        input_type="text",
        analysis_type="cooking",
        food_name=recipe.title,
        result_json=recipe.model_dump_json(),
        provider="demo" if recipe.is_demo else "openai",
        is_demo=recipe.is_demo,
    )
    db.add(record)
    db.commit()
    return recipe


@router.post("/chat", response_model=CookingChatResponse)
async def chat(
    request: CookingChatRequest,
    db: Session = Depends(get_db),
):
    """Chat with the cooking assistant about a recipe."""
    provider = get_provider()
    try:
        return await chat_about_recipe(request, provider)
    except (AIProviderError, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Cooking chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {e}")
