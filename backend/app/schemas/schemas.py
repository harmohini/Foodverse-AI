"""Pydantic schemas for all API request/response models."""
from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


# ─── Shared ────────────────────────────────────────────────────────────────

class AnalysisMetadata(BaseModel):
    analysis_id: str
    input_type: str  # image | video | audio | text
    analysis_type: str
    provider: str
    is_demo: bool
    warnings: list[str] = []
    created_at: datetime


# ─── Food Recognition ──────────────────────────────────────────────────────

class Ingredient(BaseModel):
    name: str
    confidence: Optional[float] = None


class FoodRecognitionResult(BaseModel):
    dish_name: str
    confidence: Optional[float] = None
    description: str
    ingredients: list[Ingredient] = []
    cuisine: Optional[str] = None
    serving_size_estimate: str = "1 serving"
    metadata: AnalysisMetadata


# ─── Nutrition ─────────────────────────────────────────────────────────────

class NutritionData(BaseModel):
    food_name: str
    serving_size: str
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sugar_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    nutrition_score: Optional[float] = None
    score_explanation: str = ""
    summary: str = ""
    source: str = "demo_estimate"
    uncertainty_note: str = ""


class NutritionRequest(BaseModel):
    food_name: str = Field(..., min_length=1, max_length=255)
    serving_size: str = Field(default="1 serving", max_length=100)
    ingredients: list[str] = []


class NutritionResponse(BaseModel):
    nutrition: NutritionData
    metadata: AnalysisMetadata


# ─── Freshness ─────────────────────────────────────────────────────────────

class FreshnessObservation(BaseModel):
    characteristic: str
    observation: str
    severity: str = "normal"  # normal | mild | concerning


class FreshnessResult(BaseModel):
    food_category: str
    status: str  # Fresh | Moderately Fresh | Possible Spoilage
    confidence: Optional[float] = None
    observations: list[FreshnessObservation] = []
    next_steps: list[str] = []
    safety_disclaimer: str
    metadata: AnalysisMetadata


# ─── Hygiene ───────────────────────────────────────────────────────────────

class HygieneIndicator(BaseModel):
    indicator: str
    status: str  # observed | not_observed | unable_to_assess
    evidence: str = ""
    timestamp_seconds: Optional[float] = None


class HygieneReport(BaseModel):
    overall_assessment: str
    frames_analyzed: int
    duration_seconds: Optional[float] = None
    indicators: list[HygieneIndicator] = []
    limitations: list[str] = []
    corrective_actions: list[str] = []
    disclaimer: str
    metadata: AnalysisMetadata


# ─── Cooking ───────────────────────────────────────────────────────────────

class RecipeIngredient(BaseModel):
    item: str
    quantity: str
    unit: str = ""
    preparation: str = ""


class RecipeStep(BaseModel):
    step_number: int
    instruction: str
    duration_minutes: Optional[int] = None
    tip: str = ""


class CookingRequest(BaseModel):
    dish_name: str = Field(..., min_length=1, max_length=255)
    available_ingredients: list[str] = []
    cuisine_preference: str = ""
    dietary_preference: str = ""
    cooking_time_minutes: Optional[int] = None
    difficulty: str = "medium"  # easy | medium | hard
    servings: int = Field(default=2, ge=1, le=20)


class CookingChatRequest(BaseModel):
    recipe_id: str
    message: str = Field(..., min_length=1, max_length=1000)
    chat_history: list[dict[str, str]] = []


class Recipe(BaseModel):
    recipe_id: str
    title: str
    description: str
    cuisine: str
    dietary_info: str
    prep_time_minutes: int
    cook_time_minutes: int
    servings: int
    difficulty: str
    ingredients: list[RecipeIngredient] = []
    steps: list[RecipeStep] = []
    substitutions: list[str] = []
    equipment: list[str] = []
    allergen_notes: list[str] = []
    food_safety_notes: list[str] = []
    estimated_nutrition: Optional[NutritionData] = None
    is_demo: bool = True


class CookingChatResponse(BaseModel):
    message: str
    is_demo: bool = True


# ─── Meal Planner ──────────────────────────────────────────────────────────

class MealItem(BaseModel):
    meal_type: str  # breakfast | lunch | dinner | snack
    name: str
    description: str
    ingredients: list[str] = []
    serving_size: str = "1 serving"
    prep_time_minutes: int = 15
    estimated_calories: Optional[float] = None
    brief_instructions: str = ""


class DayPlan(BaseModel):
    day: int
    date_label: str  # e.g., "Day 1 – Monday"
    meals: list[MealItem] = []
    daily_estimated_calories: Optional[float] = None


class ShoppingItem(BaseModel):
    ingredient: str
    quantity: str
    category: str  # produce | protein | dairy | pantry | other


class MealPlanRequest(BaseModel):
    dietary_pattern: str = ""  # omnivore | vegetarian | vegan | etc.
    allergies: list[str] = []
    excluded_foods: list[str] = []
    favorite_cuisines: list[str] = []
    meals_per_day: int = Field(default=3, ge=1, le=6)
    plan_days: int = Field(default=7, ge=1, le=7)
    cooking_time_preference: str = "moderate"  # quick | moderate | leisurely
    goal: str = ""
    budget_preference: str = ""


class MealPlanResponse(BaseModel):
    plan_id: str
    title: str
    days: list[DayPlan] = []
    shopping_list: list[ShoppingItem] = []
    allergy_reminder: str
    is_demo: bool = True
    created_at: datetime


class MealPlanUpdate(BaseModel):
    title: Optional[str] = None
    plan_json: Optional[str] = None


# ─── History ───────────────────────────────────────────────────────────────

class HistoryItem(BaseModel):
    id: int
    analysis_id: str
    input_type: str
    analysis_type: str
    food_name: Optional[str] = None
    provider: str
    is_demo: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Health ────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    ai_provider: str
    is_demo_mode: bool
    message: str
