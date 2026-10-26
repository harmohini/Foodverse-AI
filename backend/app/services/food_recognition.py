"""Food recognition service with demo and real provider support."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional
from app.services.ai_provider import AIProvider, DemoProvider
from app.schemas.schemas import (
    FoodRecognitionResult, Ingredient, AnalysisMetadata
)
from app.core.logging import get_logger

logger = get_logger(__name__)

DEMO_FOODS = {
    "default": {
        "dish_name": "Grilled Chicken Salad",
        "confidence": 0.87,
        "description": "A fresh grilled chicken salad with mixed greens, cherry tomatoes, cucumber, and a light vinaigrette dressing. This is a demo result — no real image analysis was performed.",
        "ingredients": [
            {"name": "Grilled chicken breast", "confidence": 0.92},
            {"name": "Mixed greens", "confidence": 0.88},
            {"name": "Cherry tomatoes", "confidence": 0.85},
            {"name": "Cucumber", "confidence": 0.80},
            {"name": "Red onion", "confidence": 0.72},
        ],
        "cuisine": "American",
        "serving_size_estimate": "1 bowl (~350g)",
    },
    "pizza": {
        "dish_name": "Margherita Pizza",
        "confidence": 0.92,
        "description": "Classic Margherita pizza with tomato sauce, fresh mozzarella, and basil on a thin crust. Demo result.",
        "ingredients": [
            {"name": "Pizza dough", "confidence": 0.95},
            {"name": "Tomato sauce", "confidence": 0.90},
            {"name": "Mozzarella cheese", "confidence": 0.93},
            {"name": "Fresh basil", "confidence": 0.88},
        ],
        "cuisine": "Italian",
        "serving_size_estimate": "2 slices (~280g)",
    },
    "sushi": {
        "dish_name": "Salmon Nigiri Sushi",
        "confidence": 0.89,
        "description": "Traditional Japanese nigiri sushi with fresh salmon over seasoned rice. Demo result.",
        "ingredients": [
            {"name": "Sushi rice", "confidence": 0.94},
            {"name": "Fresh salmon", "confidence": 0.91},
            {"name": "Nori (seaweed)", "confidence": 0.78},
            {"name": "Soy sauce", "confidence": 0.65},
        ],
        "cuisine": "Japanese",
        "serving_size_estimate": "3 pieces (~150g)",
    },
}


async def recognize_food(
    image_path: str,
    provider: AIProvider,
) -> FoodRecognitionResult:
    """Recognize food in an image using the configured provider."""
    analysis_id = uuid.uuid4().hex
    is_demo = isinstance(provider, DemoProvider)

    if is_demo:
        demo_data = DEMO_FOODS["default"]
        warnings = [
            "DEMO MODE: No real image analysis was performed.",
            "To enable live image recognition, configure AI_PROVIDER=openai and a valid OPENAI_API_KEY.",
        ]
        return FoodRecognitionResult(
            dish_name=demo_data["dish_name"],
            confidence=demo_data["confidence"],
            description=demo_data["description"],
            ingredients=[Ingredient(**i) for i in demo_data["ingredients"]],
            cuisine=demo_data["cuisine"],
            serving_size_estimate=demo_data["serving_size_estimate"],
            metadata=AnalysisMetadata(
                analysis_id=analysis_id,
                input_type="image",
                analysis_type="food_recognition",
                provider="demo",
                is_demo=True,
                warnings=warnings,
                created_at=datetime.now(timezone.utc),
            ),
        )

    # Real provider
    prompt = (
        "Analyze this food image. Return a JSON object with these keys: "
        "dish_name (string), confidence (0-1 float), description (string, 1-2 sentences), "
        "ingredients (array of {name, confidence}), cuisine (string), "
        "serving_size_estimate (string like '1 bowl ~350g'). "
        "Be honest if you are uncertain. Do not fabricate ingredients."
    )
    try:
        raw = await provider.analyze_image(image_path, prompt)
        import json
        # Extract JSON from response
        start = raw.find("{")
        end = raw.rfind("}") + 1
        data = json.loads(raw[start:end])
        return FoodRecognitionResult(
            dish_name=data.get("dish_name", "Unknown food"),
            confidence=data.get("confidence"),
            description=data.get("description", ""),
            ingredients=[Ingredient(**i) if isinstance(i, dict) else Ingredient(name=i) for i in data.get("ingredients", [])],
            cuisine=data.get("cuisine"),
            serving_size_estimate=data.get("serving_size_estimate", "1 serving"),
            metadata=AnalysisMetadata(
                analysis_id=analysis_id,
                input_type="image",
                analysis_type="food_recognition",
                provider=provider.name,
                is_demo=False,
                warnings=["Results are AI estimates. Confidence scores are model-generated and not laboratory-verified."],
                created_at=datetime.now(timezone.utc),
            ),
        )
    except Exception as e:
        logger.error(f"Food recognition failed: {e}")
        raise
