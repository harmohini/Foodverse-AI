"""SQLAlchemy ORM models."""
from datetime import datetime, timezone
from sqlalchemy import String, Text, Float, Integer, DateTime, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database.connection import Base


def utcnow():
    return datetime.now(timezone.utc)


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    analysis_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    input_type: Mapped[str] = mapped_column(String(20))  # image, video, audio, text
    analysis_type: Mapped[str] = mapped_column(String(50))  # food, nutrition, freshness, hygiene, cooking
    food_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str] = mapped_column(String(50), default="demo")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class NutritionRecord(Base):
    __tablename__ = "nutrition_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    analysis_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    food_name: Mapped[str] = mapped_column(String(255))
    serving_size: Mapped[str] = mapped_column(String(100))
    calories: Mapped[float | None] = mapped_column(Float, nullable=True)
    protein_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    fiber_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    sugar_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    sodium_mg: Mapped[float | None] = mapped_column(Float, nullable=True)
    nutrition_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(100), default="demo_estimate")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MealPlan(Base):
    __tablename__ = "meal_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    plan_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    dietary_pattern: Mapped[str | None] = mapped_column(String(100), nullable=True)
    allergies: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    excluded_foods: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    goal: Mapped[str | None] = mapped_column(String(200), nullable=True)
    meals_per_day: Mapped[int] = mapped_column(Integer, default=3)
    plan_days: Mapped[int] = mapped_column(Integer, default=7)
    plan_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # Full plan JSON
    shopping_list_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class RecipeRecord(Base):
    __tablename__ = "recipe_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recipe_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    cuisine: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dietary_pref: Mapped[str | None] = mapped_column(String(100), nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String(50), nullable=True)
    servings: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recipe_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
