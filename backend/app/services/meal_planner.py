"""Personalized meal planner service."""
from __future__ import annotations
import uuid
import json
from datetime import datetime, timezone
from fastapi import HTTPException
from app.services.ai_provider import (
    AIProvider, DemoProvider, AIProviderError, AIResponseFormatError
)
from app.schemas.schemas import (
    MealPlanRequest, MealPlanResponse, DayPlan, MealItem, ShoppingItem
)
from app.core.logging import get_logger

logger = get_logger(__name__)

ALLERGY_REMINDER = (
    "Always check ingredient labels for allergens. Cross-contamination can occur during food preparation. "
    "This meal plan is a general guide — it does not constitute medical, dietary, or clinical advice. "
    "Consult a registered dietitian for personalised nutrition planning."
)

DEMO_MEAL_PLAN = [
    {
        "day": 1, "date_label": "Day 1 – Monday",
        "meals": [
            {"meal_type": "breakfast", "name": "Greek Yogurt Parfait", "description": "Creamy Greek yogurt layered with fresh berries and granola", "ingredients": ["Greek yogurt", "Mixed berries", "Granola", "Honey"], "serving_size": "1 bowl", "prep_time_minutes": 5, "estimated_calories": 320, "brief_instructions": "Layer yogurt, berries, and granola in a bowl. Drizzle with honey."},
            {"meal_type": "lunch", "name": "Quinoa & Roasted Vegetable Bowl", "description": "Nutty quinoa with colourful roasted seasonal vegetables", "ingredients": ["Quinoa", "Zucchini", "Bell peppers", "Red onion", "Olive oil", "Lemon", "Feta cheese"], "serving_size": "1 bowl (~400g)", "prep_time_minutes": 30, "estimated_calories": 480, "brief_instructions": "Cook quinoa. Roast vegetables at 200°C for 25 minutes. Combine and dress with lemon and olive oil."},
            {"meal_type": "dinner", "name": "Baked Salmon with Steamed Broccoli", "description": "Omega-3-rich salmon fillet with garlic-steamed broccoli", "ingredients": ["Salmon fillet", "Broccoli", "Garlic", "Lemon", "Olive oil", "Salt", "Pepper"], "serving_size": "1 plate (~450g)", "prep_time_minutes": 25, "estimated_calories": 520, "brief_instructions": "Season salmon. Bake at 200°C for 12–15 minutes until internal temp reaches 63°C. Steam broccoli 5 minutes."},
        ],
        "daily_estimated_calories": 1320,
    },
    {
        "day": 2, "date_label": "Day 2 – Tuesday",
        "meals": [
            {"meal_type": "breakfast", "name": "Avocado Toast with Poached Eggs", "description": "Creamy avocado on wholegrain toast topped with runny poached eggs", "ingredients": ["Wholegrain bread", "Avocado", "Eggs", "Lemon juice", "Chilli flakes", "Salt"], "serving_size": "2 slices", "prep_time_minutes": 10, "estimated_calories": 380, "brief_instructions": "Toast bread. Mash avocado with lemon. Poach eggs 3–4 minutes. Assemble."},
            {"meal_type": "lunch", "name": "Lentil Soup with Crusty Bread", "description": "Hearty, protein-rich red lentil soup with warming spices", "ingredients": ["Red lentils", "Carrots", "Celery", "Onion", "Garlic", "Cumin", "Coriander", "Wholegrain bread"], "serving_size": "1 bowl + 1 slice", "prep_time_minutes": 35, "estimated_calories": 440, "brief_instructions": "Sauté vegetables. Add lentils and stock. Simmer 25 minutes. Blend partially. Season."},
            {"meal_type": "dinner", "name": "Chicken Stir-Fry with Brown Rice", "description": "Lean chicken breast with colourful stir-fried vegetables over brown rice", "ingredients": ["Chicken breast", "Brown rice", "Broccoli", "Snap peas", "Carrots", "Soy sauce", "Ginger", "Garlic", "Sesame oil"], "serving_size": "1 plate (~500g)", "prep_time_minutes": 30, "estimated_calories": 560, "brief_instructions": "Cook rice. Stir-fry chicken to 74°C internal temp. Add vegetables. Season with soy, ginger, garlic."},
        ],
        "daily_estimated_calories": 1380,
    },
    {
        "day": 3, "date_label": "Day 3 – Wednesday",
        "meals": [
            {"meal_type": "breakfast", "name": "Overnight Oats", "description": "Rolled oats soaked overnight with chia seeds and fresh fruit", "ingredients": ["Rolled oats", "Milk or plant milk", "Chia seeds", "Banana", "Cinnamon", "Maple syrup"], "serving_size": "1 jar", "prep_time_minutes": 5, "estimated_calories": 340, "brief_instructions": "Mix oats, milk, chia. Refrigerate overnight. Top with banana and maple syrup."},
            {"meal_type": "lunch", "name": "Mediterranean Wrap", "description": "Wholegrain wrap filled with hummus, falafels, and fresh salad", "ingredients": ["Wholegrain wrap", "Hummus", "Falafel", "Cucumber", "Tomato", "Lettuce", "Tzatziki"], "serving_size": "1 wrap", "prep_time_minutes": 10, "estimated_calories": 420, "brief_instructions": "Spread hummus. Add falafel, cucumber, tomato, lettuce. Drizzle tzatziki. Wrap tightly."},
            {"meal_type": "dinner", "name": "Beef Tacos with Fresh Salsa", "description": "Seasoned lean beef in corn tortillas with fresh tomato salsa and avocado", "ingredients": ["Lean ground beef", "Corn tortillas", "Tomatoes", "Red onion", "Coriander", "Lime", "Avocado", "Cumin", "Paprika"], "serving_size": "3 tacos", "prep_time_minutes": 25, "estimated_calories": 580, "brief_instructions": "Cook beef to 70°C, season with cumin and paprika. Make salsa. Warm tortillas. Assemble."},
        ],
        "daily_estimated_calories": 1340,
    },
]

DEMO_SHOPPING_LIST = [
    {"ingredient": "Greek yogurt", "quantity": "500g", "category": "dairy"},
    {"ingredient": "Mixed berries", "quantity": "300g", "category": "produce"},
    {"ingredient": "Granola", "quantity": "200g", "category": "pantry"},
    {"ingredient": "Honey", "quantity": "1 jar", "category": "pantry"},
    {"ingredient": "Quinoa", "quantity": "300g", "category": "pantry"},
    {"ingredient": "Salmon fillets", "quantity": "2 x 180g", "category": "protein"},
    {"ingredient": "Chicken breast", "quantity": "500g", "category": "protein"},
    {"ingredient": "Lean ground beef", "quantity": "400g", "category": "protein"},
    {"ingredient": "Eggs", "quantity": "6", "category": "protein"},
    {"ingredient": "Avocados", "quantity": "3", "category": "produce"},
    {"ingredient": "Broccoli", "quantity": "2 heads", "category": "produce"},
    {"ingredient": "Carrots", "quantity": "500g", "category": "produce"},
    {"ingredient": "Bell peppers", "quantity": "3", "category": "produce"},
    {"ingredient": "Tomatoes", "quantity": "500g", "category": "produce"},
    {"ingredient": "Red lentils", "quantity": "400g", "category": "pantry"},
    {"ingredient": "Brown rice", "quantity": "500g", "category": "pantry"},
    {"ingredient": "Wholegrain bread", "quantity": "1 loaf", "category": "pantry"},
    {"ingredient": "Olive oil", "quantity": "1 bottle", "category": "pantry"},
    {"ingredient": "Lemons", "quantity": "4", "category": "produce"},
]


def _filter_for_exclusions(meals: list[dict], excluded_foods: list[str]) -> list[dict]:
    """Remove meals containing excluded foods (basic filter)."""
    if not excluded_foods:
        return meals
    exclusions = [e.lower() for e in excluded_foods]
    filtered = []
    for meal in meals:
        ingredients_str = " ".join(meal.get("ingredients", [])).lower()
        if not any(exc in ingredients_str for exc in exclusions):
            filtered.append(meal)
    return filtered


async def generate_meal_plan(
    request: MealPlanRequest,
    provider: AIProvider,
) -> MealPlanResponse:
    """Generate a meal plan using the configured provider."""
    plan_id = uuid.uuid4().hex
    is_demo = isinstance(provider, DemoProvider)
    days_count = min(request.plan_days, 7)

    if is_demo:
        # Use demo plan (repeating for requested days)
        days_out = []
        for i in range(days_count):
            demo_day = DEMO_MEAL_PLAN[i % len(DEMO_MEAL_PLAN)]
            # Filter excluded foods
            filtered_meals = _filter_for_exclusions(demo_day["meals"], request.excluded_foods)
            day = DayPlan(
                day=i + 1,
                date_label=f"Day {i+1}",
                meals=[MealItem(**m) for m in filtered_meals],
                daily_estimated_calories=sum(m.get("estimated_calories", 0) for m in filtered_meals),
            )
            days_out.append(day)

        return MealPlanResponse(
            plan_id=plan_id,
            title=f"Demo {days_count}-Day Meal Plan",
            days=days_out,
            shopping_list=[ShoppingItem(**s) for s in DEMO_SHOPPING_LIST],
            allergy_reminder=ALLERGY_REMINDER,
            is_demo=True,
            created_at=datetime.now(timezone.utc),
        )

    # Real provider
    exclusions_str = ", ".join(request.excluded_foods) if request.excluded_foods else "none"
    allergies_str = ", ".join(request.allergies) if request.allergies else "none"
    prompt = (
        f"Create a {days_count}-day meal plan. "
        f"Dietary pattern: {request.dietary_pattern or 'balanced omnivore'}. "
        f"Allergies to avoid: {allergies_str}. "
        f"Foods to exclude: {exclusions_str}. "
        f"Cuisines preferred: {', '.join(request.favorite_cuisines) or 'varied'}. "
        f"Meals per day: {request.meals_per_day}. "
        f"Cooking time preference: {request.cooking_time_preference}. "
        f"Goal: {request.goal or 'balanced eating'}. "
        "Return a JSON with: title (string), days (array of {day, date_label, meals: [{meal_type, name, description, ingredients, serving_size, prep_time_minutes, estimated_calories, brief_instructions}], daily_estimated_calories}), "
        "shopping_list (array of {ingredient, quantity, category}). "
        "CRITICAL: Do NOT include any allergens listed above. Double-check each meal."
    )
    system = (
        "You are a professional meal planning dietitian. Create practical, balanced, enjoyable meal plans. "
        "Always respect allergies and exclusions. Do not prescribe clinical diets or make medical claims."
    )
    try:
        raw = await provider.generate_text(prompt, system)
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end <= start:
            raise AIResponseFormatError("AI provider did not return valid JSON for meal plan.")
        data = json.loads(raw[start:end])
        days_out = [
            DayPlan(
                day=d.get("day", i+1),
                date_label=d.get("date_label", f"Day {i+1}"),
                meals=[MealItem(**m) if isinstance(m, dict) else MealItem(meal_type="meal", name=str(m), description="") for m in d.get("meals", [])],
                daily_estimated_calories=d.get("daily_estimated_calories"),
            )
            for i, d in enumerate(data.get("days", []))
        ]
        return MealPlanResponse(
            plan_id=plan_id,
            title=data.get("title", f"{days_count}-Day Meal Plan"),
            days=days_out,
            shopping_list=[ShoppingItem(**s) if isinstance(s, dict) else ShoppingItem(ingredient=str(s), quantity="1", category="other") for s in data.get("shopping_list", [])],
            allergy_reminder=ALLERGY_REMINDER,
            is_demo=False,
            created_at=datetime.now(timezone.utc),
        )
    except (AIProviderError, HTTPException):
        raise
    except json.JSONDecodeError as exc:
        logger.error(f"Failed to parse meal plan JSON: {exc}")
        raise AIResponseFormatError("AI meal plan response contained invalid JSON.") from exc
    except Exception as e:
        logger.error(f"Meal plan generation failed: {e}")
        raise
