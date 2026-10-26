"""Smart cooking assistant service."""
from __future__ import annotations
import uuid
import json
from datetime import datetime, timezone
from app.services.ai_provider import AIProvider, DemoProvider
from app.schemas.schemas import (
    Recipe, RecipeIngredient, RecipeStep, CookingRequest,
    CookingChatRequest, CookingChatResponse, NutritionData
)
from app.core.logging import get_logger

logger = get_logger(__name__)

DEMO_RECIPES = {
    "default": {
        "title": "Herb-Roasted Chicken with Vegetables",
        "description": "A classic, comforting roast with golden-skinned chicken and seasonal vegetables. This is a demo recipe — AI generation requires a configured provider.",
        "cuisine": "American",
        "dietary_info": "Gluten-free, dairy-free",
        "prep_time_minutes": 20,
        "cook_time_minutes": 60,
        "servings": 4,
        "difficulty": "medium",
        "ingredients": [
            {"item": "Whole chicken", "quantity": "1", "unit": "kg", "preparation": "patted dry"},
            {"item": "Olive oil", "quantity": "3", "unit": "tbsp", "preparation": ""},
            {"item": "Garlic cloves", "quantity": "4", "unit": "", "preparation": "minced"},
            {"item": "Fresh rosemary", "quantity": "2", "unit": "sprigs", "preparation": "leaves stripped"},
            {"item": "Thyme", "quantity": "1", "unit": "tsp", "preparation": "dried"},
            {"item": "Carrots", "quantity": "3", "unit": "medium", "preparation": "cut into chunks"},
            {"item": "Potatoes", "quantity": "4", "unit": "medium", "preparation": "quartered"},
            {"item": "Onion", "quantity": "1", "unit": "large", "preparation": "roughly chopped"},
            {"item": "Salt", "quantity": "1.5", "unit": "tsp", "preparation": ""},
            {"item": "Black pepper", "quantity": "0.5", "unit": "tsp", "preparation": ""},
        ],
        "steps": [
            {"step_number": 1, "instruction": "Preheat your oven to 200°C (400°F). Pat the chicken dry with paper towels — this ensures crispy skin.", "duration_minutes": 10, "tip": "Drying the chicken is key to golden, crispy skin."},
            {"step_number": 2, "instruction": "In a small bowl, mix olive oil, minced garlic, rosemary, thyme, salt, and pepper. Rub this mixture all over the chicken, including under the skin.", "duration_minutes": 5, "tip": ""},
            {"step_number": 3, "instruction": "Arrange carrots, potatoes, and onion in a roasting pan. Place the chicken on top of the vegetables.", "duration_minutes": 5, "tip": "The vegetables act as a natural rack."},
            {"step_number": 4, "instruction": "Roast for 60 minutes, or until the internal temperature at the thickest part of the thigh reaches 74°C (165°F).", "duration_minutes": 60, "tip": "Use a meat thermometer for food safety."},
            {"step_number": 5, "instruction": "Rest the chicken for 10 minutes before carving. This lets the juices redistribute.", "duration_minutes": 10, "tip": ""},
        ],
        "substitutions": [
            "Chicken thighs can replace a whole chicken — reduce cooking time to 35–40 minutes.",
            "Sweet potatoes work well in place of regular potatoes.",
            "Dried herbs can replace fresh — use one-third the amount.",
        ],
        "equipment": ["Roasting pan", "Meat thermometer", "Basting brush", "Sharp carving knife"],
        "allergen_notes": ["Contains no common allergens in this base recipe. Check any added seasoning mixes for allergens."],
        "food_safety_notes": [
            "Always cook poultry to an internal temperature of 74°C (165°F).",
            "Do not rinse raw chicken — this spreads bacteria; pat dry instead.",
            "Wash hands and surfaces thoroughly after handling raw chicken.",
        ],
        "estimated_nutrition": {
            "food_name": "Herb-Roasted Chicken with Vegetables",
            "serving_size": "1 serving (~350g)",
            "calories": 420, "protein_g": 38, "carbs_g": 28, "fat_g": 16,
            "fiber_g": 4, "sugar_g": 5, "sodium_mg": 610,
            "nutrition_score": 72,
            "score_explanation": "Good protein and fiber. Moderate sodium.",
            "summary": "A balanced meal with good protein and vegetables.",
            "source": "demo_estimate",
            "uncertainty_note": "Demo estimate. Actual values vary.",
        },
    },
}

DEMO_CHAT_RESPONSES = {
    "vegetarian": "To make this recipe vegetarian, omit the chicken and add 1 can of chickpeas and 2 cups of cauliflower florets. Roast the vegetables at 200°C for 40 minutes until golden.",
    "butter": "Yes! You can replace butter with olive oil in a 3:4 ratio (e.g., 3 tbsp butter → 2.25 tbsp olive oil). The flavor will be slightly different but still delicious.",
    "time": "To reduce preparation time, use pre-cut vegetable packs from the supermarket, and substitute a whole chicken with bone-in thighs, which cook in about 35 minutes.",
    "default": "Great question! In demo mode, I can share general cooking tips. To enable AI-powered chat responses, configure an AI provider in your settings. In the meantime, feel free to adjust seasonings to your taste and consult the food safety notes.",
}


async def generate_recipe(
    request: CookingRequest,
    provider: AIProvider,
) -> Recipe:
    """Generate a recipe using the configured provider."""
    recipe_id = uuid.uuid4().hex
    is_demo = isinstance(provider, DemoProvider)

    if is_demo:
        demo = DEMO_RECIPES["default"]
        return Recipe(
            recipe_id=recipe_id,
            is_demo=True,
            **{k: v for k, v in demo.items() if k != "estimated_nutrition"},
            estimated_nutrition=NutritionData(**demo["estimated_nutrition"]),
        )

    # Real provider path
    ingredients_str = ", ".join(request.available_ingredients) if request.available_ingredients else "pantry staples"
    prompt = (
        f"Generate a detailed recipe for: {request.dish_name}. "
        f"Available ingredients: {ingredients_str}. "
        f"Cuisine: {request.cuisine_preference or 'any'}. "
        f"Dietary preference: {request.dietary_preference or 'none'}. "
        f"Max cooking time: {request.cooking_time_minutes or 60} minutes. "
        f"Difficulty: {request.difficulty}. Servings: {request.servings}. "
        "Return a JSON object with keys: title, description, cuisine, dietary_info, "
        "prep_time_minutes, cook_time_minutes, servings, difficulty, "
        "ingredients (array of {item, quantity, unit, preparation}), "
        "steps (array of {step_number, instruction, duration_minutes, tip}), "
        "substitutions (array of strings), equipment (array of strings), "
        "allergen_notes (array of strings), food_safety_notes (array of strings), "
        "estimated_nutrition {food_name, serving_size, calories, protein_g, carbs_g, fat_g, fiber_g}."
    )
    system = "You are a professional chef and food safety expert. Generate safe, practical, and delicious recipes. Always include food safety reminders, especially for meat, poultry, and eggs."
    try:
        raw = await provider.generate_text(prompt, system)
        start = raw.find("{")
        end = raw.rfind("}") + 1
        data = json.loads(raw[start:end])
        en = data.get("estimated_nutrition", {})
        nutrition = NutritionData(
            food_name=en.get("food_name", request.dish_name),
            serving_size=en.get("serving_size", f"1 serving"),
            calories=en.get("calories"),
            protein_g=en.get("protein_g"),
            carbs_g=en.get("carbs_g"),
            fat_g=en.get("fat_g"),
            fiber_g=en.get("fiber_g"),
            source=f"ai_estimate:{provider.name}",
            uncertainty_note="AI-generated nutritional estimate. Actual values vary.",
        ) if en else None
        return Recipe(
            recipe_id=recipe_id,
            title=data.get("title", request.dish_name),
            description=data.get("description", ""),
            cuisine=data.get("cuisine", request.cuisine_preference or ""),
            dietary_info=data.get("dietary_info", request.dietary_preference or ""),
            prep_time_minutes=data.get("prep_time_minutes", 15),
            cook_time_minutes=data.get("cook_time_minutes", 30),
            servings=data.get("servings", request.servings),
            difficulty=data.get("difficulty", request.difficulty),
            ingredients=[RecipeIngredient(**i) if isinstance(i, dict) else RecipeIngredient(item=str(i), quantity="") for i in data.get("ingredients", [])],
            steps=[RecipeStep(**s) if isinstance(s, dict) else RecipeStep(step_number=idx+1, instruction=str(s)) for idx, s in enumerate(data.get("steps", []))],
            substitutions=data.get("substitutions", []),
            equipment=data.get("equipment", []),
            allergen_notes=data.get("allergen_notes", []),
            food_safety_notes=data.get("food_safety_notes", ["Always cook food to safe internal temperatures."]),
            estimated_nutrition=nutrition,
            is_demo=False,
        )
    except Exception as e:
        logger.error(f"Recipe generation failed: {e}")
        raise


async def chat_about_recipe(
    request: CookingChatRequest,
    provider: AIProvider,
) -> CookingChatResponse:
    """Handle a chat follow-up about a recipe."""
    is_demo = isinstance(provider, DemoProvider)

    if is_demo:
        message_lower = request.message.lower()
        response = DEMO_CHAT_RESPONSES["default"]
        for key, val in DEMO_CHAT_RESPONSES.items():
            if key in message_lower:
                response = val
                break
        return CookingChatResponse(
            message=f"[DEMO MODE] {response}",
            is_demo=True,
        )

    system = (
        "You are FoodVerse AI's cooking assistant. Help with recipe modifications, substitutions, "
        "and cooking questions. Always include food safety reminders where relevant. "
        "Be concise and practical."
    )
    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in request.chat_history[-6:]])
    prompt = f"{history_text}\nUser: {request.message}" if history_text else request.message

    try:
        response = await provider.generate_text(prompt, system)
        return CookingChatResponse(message=response, is_demo=False)
    except Exception as e:
        logger.error(f"Cooking chat failed: {e}")
        raise
