"""Nutrition analysis service."""
from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from app.services.ai_provider import AIProvider, DemoProvider, AIProviderError, AIResponseFormatError
from app.schemas.schemas import NutritionData, NutritionResponse, AnalysisMetadata, NutritionRequest
from app.core.logging import get_logger

logger = get_logger(__name__)

# Demo nutrition database (approximate values per stated serving)
DEMO_NUTRITION = {
    "grilled chicken salad": {
        "calories": 280, "protein_g": 32, "carbs_g": 12, "fat_g": 10,
        "fiber_g": 4, "sugar_g": 5, "sodium_mg": 420,
        "serving_size": "1 bowl (~350g)",
    },
    "margherita pizza": {
        "calories": 580, "protein_g": 22, "carbs_g": 72, "fat_g": 22,
        "fiber_g": 3, "sugar_g": 8, "sodium_mg": 890,
        "serving_size": "2 slices (~280g)",
    },
    "salmon nigiri sushi": {
        "calories": 210, "protein_g": 16, "carbs_g": 26, "fat_g": 4,
        "fiber_g": 0.5, "sugar_g": 2, "sodium_mg": 380,
        "serving_size": "3 pieces (~150g)",
    },
    "caesar salad": {
        "calories": 350, "protein_g": 12, "carbs_g": 20, "fat_g": 24,
        "fiber_g": 3, "sugar_g": 3, "sodium_mg": 620,
        "serving_size": "1 bowl (~300g)",
    },
    "pasta carbonara": {
        "calories": 650, "protein_g": 24, "carbs_g": 78, "fat_g": 26,
        "fiber_g": 3, "sugar_g": 4, "sodium_mg": 720,
        "serving_size": "1 plate (~400g)",
    },
    "oatmeal": {
        "calories": 158, "protein_g": 6, "carbs_g": 27, "fat_g": 3,
        "fiber_g": 4, "sugar_g": 1, "sodium_mg": 6,
        "serving_size": "1 cup cooked (~240g)",
    },
    "avocado toast": {
        "calories": 320, "protein_g": 10, "carbs_g": 36, "fat_g": 16,
        "fiber_g": 8, "sugar_g": 2, "sodium_mg": 380,
        "serving_size": "2 slices (~200g)",
    },
}

DEFAULT_DEMO = {
    "calories": 380, "protein_g": 18, "carbs_g": 45, "fat_g": 14,
    "fiber_g": 4, "sugar_g": 6, "sodium_mg": 520,
    "serving_size": "1 serving",
}


def _compute_nutrition_score(n: dict) -> tuple[float, str]:
    """
    Compute a simple nutrition score (0-100) based on macro balance.
    This is a simplified educational heuristic, NOT a medical judgment.
    """
    score = 50.0
    explanations = []

    calories = n.get("calories", 400)
    protein_g = n.get("protein_g", 15)
    fiber_g = n.get("fiber_g", 3)
    sodium_mg = n.get("sodium_mg", 600)
    fat_g = n.get("fat_g", 15)

    # Protein bonus
    if protein_g >= 20:
        score += 10
        explanations.append("Good protein content (+10)")
    elif protein_g >= 10:
        score += 5
        explanations.append("Moderate protein (+5)")

    # Fiber bonus
    if fiber_g >= 5:
        score += 10
        explanations.append("High fiber (+10)")
    elif fiber_g >= 3:
        score += 5
        explanations.append("Moderate fiber (+5)")

    # Sodium penalty
    if sodium_mg > 1000:
        score -= 15
        explanations.append("High sodium (>1000mg, -15)")
    elif sodium_mg > 600:
        score -= 5
        explanations.append("Elevated sodium (-5)")

    # Calorie density
    if calories < 200:
        score += 5
        explanations.append("Low calorie (+5)")
    elif calories > 800:
        score -= 10
        explanations.append("High calorie density (-10)")

    score = max(0, min(100, score))
    explanation = (
        f"Score: {score:.0f}/100. Calculated from protein, fiber, sodium, and calorie density. "
        f"Details: {'; '.join(explanations)}. "
        "This is an educational estimate — not a medical or dietary recommendation."
    )
    return round(score, 1), explanation


async def analyze_nutrition(
    request: NutritionRequest,
    provider: AIProvider,
) -> NutritionResponse:
    """Return nutrition estimates for the given food."""
    analysis_id = uuid.uuid4().hex
    is_demo = isinstance(provider, DemoProvider)
    food_key = request.food_name.lower().strip()

    if is_demo:
        # Look up demo data
        matched = None
        for key, val in DEMO_NUTRITION.items():
            if key in food_key or food_key in key:
                matched = val
                break
        n = matched or DEFAULT_DEMO

        serving_size = request.serving_size if request.serving_size != "1 serving" else n["serving_size"]
        score, score_exp = _compute_nutrition_score(n)

        nutrition = NutritionData(
            food_name=request.food_name,
            serving_size=serving_size,
            calories=n["calories"],
            protein_g=n["protein_g"],
            carbs_g=n["carbs_g"],
            fat_g=n["fat_g"],
            fiber_g=n["fiber_g"],
            sugar_g=n["sugar_g"],
            sodium_mg=n["sodium_mg"],
            nutrition_score=score,
            score_explanation=score_exp,
            summary=(
                f"Estimated nutrition for {request.food_name} ({serving_size}): "
                f"approximately {n['calories']} kcal, {n['protein_g']}g protein, "
                f"{n['carbs_g']}g carbohydrates, {n['fat_g']}g fat."
            ),
            source="demo_reference_database",
            uncertainty_note=(
                "DEMO MODE: Values are approximate reference figures from a demo dataset. "
                "Actual nutritional content varies by recipe, preparation method, and portion size. "
                "Consult a registered dietitian for personalized dietary advice."
            ),
        )
        return NutritionResponse(
            nutrition=nutrition,
            metadata=AnalysisMetadata(
                analysis_id=analysis_id,
                input_type="text",
                analysis_type="nutrition",
                provider="demo",
                is_demo=True,
                warnings=[
                    "DEMO MODE: No real nutrition database query was performed.",
                    "Values are illustrative estimates only.",
                ],
                created_at=datetime.now(timezone.utc),
            ),
        )

    # Real provider path
    prompt = (
        f"Provide approximate nutritional information for: {request.food_name}, "
        f"serving size: {request.serving_size}. "
        f"{'Ingredients context: ' + ', '.join(request.ingredients) if request.ingredients else ''} "
        "Return a JSON object with keys: calories (kcal), protein_g, carbs_g, fat_g, fiber_g, sugar_g, sodium_mg. "
        "All values should be numbers. Be clear these are estimates."
    )
    system = "You are a nutrition estimation assistant. Provide approximate nutritional values. Always clarify these are estimates, not laboratory measurements."
    try:
        raw = await provider.generate_text(prompt, system)
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end <= start:
            raise AIResponseFormatError("AI provider did not return valid JSON for nutrition data.")
        data = json.loads(raw[start:end])
        n_data = {
            "calories": float(data.get("calories", 380)),
            "protein_g": float(data.get("protein_g", 18)),
            "carbs_g": float(data.get("carbs_g", 45)),
            "fat_g": float(data.get("fat_g", 14)),
            "fiber_g": float(data.get("fiber_g", 4)),
            "sugar_g": float(data.get("sugar_g", 6)),
            "sodium_mg": float(data.get("sodium_mg", 520)),
        }
        score, score_exp = _compute_nutrition_score(n_data)
        nutrition = NutritionData(
            food_name=request.food_name,
            serving_size=request.serving_size,
            **n_data,
            nutrition_score=score,
            score_explanation=score_exp,
            summary=f"AI-estimated nutrition for {request.food_name} ({request.serving_size}).",
            source=f"ai_estimate:{provider.name}",
            uncertainty_note=(
                "Values are AI-generated estimates. Actual nutrition varies by preparation and ingredients. "
                "Not a substitute for professional dietary advice."
            ),
        )
        return NutritionResponse(
            nutrition=nutrition,
            metadata=AnalysisMetadata(
                analysis_id=analysis_id,
                input_type="text",
                analysis_type="nutrition",
                provider=provider.name,
                is_demo=False,
                warnings=["AI-generated estimates only. Not laboratory-verified."],
                created_at=datetime.now(timezone.utc),
            ),
        )
    except (AIProviderError, HTTPException):
        raise
    except json.JSONDecodeError as exc:
        logger.error(f"Failed to parse nutrition JSON: {exc}")
        raise AIResponseFormatError("AI nutrition response contained invalid JSON.") from exc
    except Exception as e:
        logger.error(f"Nutrition analysis failed: {e}")
        raise


async def analyze_nutrition_image(
    image_path: str,
    serving_size: str,
    provider: AIProvider,
) -> NutritionResponse:
    """Estimate nutrition from an image using the configured provider."""
    analysis_id = uuid.uuid4().hex
    is_demo = isinstance(provider, DemoProvider)

    if is_demo:
        demo = DEMO_NUTRITION["grilled chicken salad"]
        serving = serving_size if serving_size and serving_size != "1 serving" else demo["serving_size"]
        score, score_exp = _compute_nutrition_score(demo)
        nutrition = NutritionData(
            food_name="Grilled Chicken Salad (Demo)",
            serving_size=serving,
            calories=demo["calories"],
            protein_g=demo["protein_g"],
            carbs_g=demo["carbs_g"],
            fat_g=demo["fat_g"],
            fiber_g=demo["fiber_g"],
            sugar_g=demo["sugar_g"],
            sodium_mg=demo["sodium_mg"],
            nutrition_score=score,
            score_explanation=score_exp,
            summary=f"Demo nutrition estimates from image for Grilled Chicken Salad ({serving}).",
            source="demo_reference_database",
            uncertainty_note="DEMO MODE: Image analysis was simulated.",
        )
        return NutritionResponse(
            nutrition=nutrition,
            metadata=AnalysisMetadata(
                analysis_id=analysis_id,
                input_type="image",
                analysis_type="nutrition",
                provider="demo",
                is_demo=True,
                warnings=["DEMO MODE: Image analysis was simulated. Estimates only."],
                created_at=datetime.now(timezone.utc),
            ),
        )

    prompt = (
        f"Analyze this food image and estimate its nutritional values. "
        f"Serving size context: {serving_size or '1 serving'}. "
        "Return a JSON object with keys: food_name (string), calories (kcal, number), "
        "protein_g (number), carbs_g (number), fat_g (number), fiber_g (number), "
        "sugar_g (number), sodium_mg (number). "
        "All values must be numbers. Be clear these are estimates."
    )
    try:
        raw = await provider.analyze_image(image_path, prompt)
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end <= start:
            raise AIResponseFormatError("AI provider did not return valid JSON for nutrition data.")
        data = json.loads(raw[start:end])
        n_data = {
            "calories": float(data.get("calories", 380)),
            "protein_g": float(data.get("protein_g", 18)),
            "carbs_g": float(data.get("carbs_g", 45)),
            "fat_g": float(data.get("fat_g", 14)),
            "fiber_g": float(data.get("fiber_g", 4)),
            "sugar_g": float(data.get("sugar_g", 6)),
            "sodium_mg": float(data.get("sodium_mg", 520)),
        }
        score, score_exp = _compute_nutrition_score(n_data)
        food_name = data.get("food_name", "Identified Food")
        actual_serving = serving_size or data.get("serving_size", "1 serving")
        nutrition = NutritionData(
            food_name=food_name,
            serving_size=actual_serving,
            **n_data,
            nutrition_score=score,
            score_explanation=score_exp,
            summary=f"AI-estimated nutrition from image for {food_name} ({actual_serving}).",
            source=f"ai_estimate:{provider.name}",
            uncertainty_note=(
                "Values are AI-generated visual estimates. Actual nutrition varies by ingredients and preparation."
            ),
        )
        return NutritionResponse(
            nutrition=nutrition,
            metadata=AnalysisMetadata(
                analysis_id=analysis_id,
                input_type="image",
                analysis_type="nutrition",
                provider=provider.name,
                is_demo=False,
                warnings=["AI visual estimates only. Not laboratory-verified."],
                created_at=datetime.now(timezone.utc),
            ),
        )
    except (AIProviderError, HTTPException):
        raise
    except json.JSONDecodeError as exc:
        logger.error(f"Failed to parse nutrition JSON: {exc}")
        raise AIResponseFormatError("AI nutrition response contained invalid JSON.") from exc
    except Exception as e:
        logger.error(f"Nutrition image analysis failed: {e}")
        raise
