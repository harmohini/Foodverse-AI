"""Meal plan management routes."""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import MealPlan, AnalysisHistory
from app.services.meal_planner import generate_meal_plan
from app.services.ai_provider import get_provider, AIProviderError
from app.schemas.schemas import MealPlanRequest, MealPlanResponse, MealPlanUpdate
from app.core.logging import get_logger

router = APIRouter(prefix="/api/v1/meal-plans", tags=["meal-plans"])
logger = get_logger(__name__)


@router.post("/generate", response_model=MealPlanResponse)
async def generate(
    request: MealPlanRequest,
    db: Session = Depends(get_db),
):
    """Generate a new meal plan."""
    provider = get_provider()
    try:
        plan = await generate_meal_plan(request, provider)
    except (AIProviderError, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Meal plan generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Meal plan generation failed: {e}")

    mp = MealPlan(
        plan_id=plan.plan_id,
        title=plan.title,
        dietary_pattern=request.dietary_pattern,
        allergies=json.dumps(request.allergies),
        excluded_foods=json.dumps(request.excluded_foods),
        goal=request.goal,
        meals_per_day=request.meals_per_day,
        plan_days=request.plan_days,
        plan_json=plan.model_dump_json(),
        shopping_list_json=json.dumps([s.model_dump() for s in plan.shopping_list]),
        is_demo=plan.is_demo,
    )
    db.add(mp)

    # Also persist to AnalysisHistory so meal plans appear in analysis history
    history_record = AnalysisHistory(
        analysis_id=plan.plan_id,
        input_type="text",
        analysis_type="meal_plan",
        food_name=plan.title,
        result_json=plan.model_dump_json(),
        provider="demo" if plan.is_demo else "openai",
        is_demo=plan.is_demo,
    )
    db.add(history_record)

    db.commit()
    return plan


@router.get("/", response_model=list[dict])
async def list_plans(db: Session = Depends(get_db)):
    """List all saved meal plans."""
    plans = db.query(MealPlan).order_by(MealPlan.created_at.desc()).all()
    return [
        {
            "id": p.id,
            "plan_id": p.plan_id,
            "title": p.title,
            "dietary_pattern": p.dietary_pattern,
            "goal": p.goal,
            "meals_per_day": p.meals_per_day,
            "plan_days": p.plan_days,
            "is_demo": p.is_demo,
            "created_at": p.created_at.isoformat(),
        }
        for p in plans
    ]


@router.get("/{plan_id}", response_model=MealPlanResponse)
async def get_plan(plan_id: str, db: Session = Depends(get_db)):
    """Retrieve a specific meal plan by ID."""
    mp = db.query(MealPlan).filter(MealPlan.plan_id == plan_id).first()
    if not mp:
        raise HTTPException(status_code=404, detail="Meal plan not found.")
    return MealPlanResponse.model_validate_json(mp.plan_json)


@router.put("/{plan_id}")
async def update_plan(plan_id: str, update: MealPlanUpdate, db: Session = Depends(get_db)):
    """Update meal plan metadata."""
    mp = db.query(MealPlan).filter(MealPlan.plan_id == plan_id).first()
    if not mp:
        raise HTTPException(status_code=404, detail="Meal plan not found.")
    if update.title is not None:
        mp.title = update.title
    if update.plan_json is not None:
        mp.plan_json = update.plan_json
    db.commit()
    return {"status": "updated"}


@router.delete("/{plan_id}")
async def delete_plan(plan_id: str, db: Session = Depends(get_db)):
    """Delete a meal plan."""
    mp = db.query(MealPlan).filter(MealPlan.plan_id == plan_id).first()
    if not mp:
        raise HTTPException(status_code=404, detail="Meal plan not found.")
    db.delete(mp)
    db.commit()
    return {"status": "deleted"}
