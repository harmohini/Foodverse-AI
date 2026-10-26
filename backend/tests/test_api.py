"""Backend tests for FoodVerse AI."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ─── Health ────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_health(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "is_demo_mode" in data


@pytest.mark.anyio
async def test_readiness(client):
    r = await client.get("/api/health/ready")
    assert r.status_code == 200
    assert r.json()["status"] == "ready"


# ─── Root ──────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_root(client):
    r = await client.get("/")
    assert r.status_code == 200
    assert r.json()["name"] == "FoodVerse AI"


# ─── Food Recognition ──────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_food_recognize_no_file(client):
    r = await client.post("/api/v1/food/recognize")
    assert r.status_code == 422  # missing required field


@pytest.mark.anyio
async def test_food_recognize_invalid_type(client):
    import io
    fake_file = io.BytesIO(b"not an image")
    r = await client.post(
        "/api/v1/food/recognize",
        files={"file": ("test.txt", fake_file, "text/plain")},
    )
    assert r.status_code == 415


@pytest.mark.anyio
async def test_food_recognize_demo(client):
    """Demo food recognition returns a valid result."""
    from PIL import Image
    import io
    img = Image.new("RGB", (100, 100), color=(200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    r = await client.post(
        "/api/v1/food/recognize",
        files={"file": ("food.jpg", buf, "image/jpeg")},
    )
    assert r.status_code == 200
    data = r.json()
    assert "dish_name" in data
    assert data["metadata"]["is_demo"] is True
    assert data["metadata"]["provider"] == "demo"


# ─── Nutrition ─────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_nutrition_analyze_demo(client):
    r = await client.post(
        "/api/v1/nutrition/analyze",
        json={"food_name": "Grilled Chicken Salad", "serving_size": "1 bowl"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["nutrition"]["calories"] is not None
    assert data["metadata"]["is_demo"] is True


@pytest.mark.anyio
async def test_nutrition_missing_food_name(client):
    r = await client.post("/api/v1/nutrition/analyze", json={"food_name": "", "serving_size": "1 serving"})
    assert r.status_code == 422


@pytest.mark.anyio
async def test_nutrition_score_present(client):
    r = await client.post(
        "/api/v1/nutrition/analyze",
        json={"food_name": "Oatmeal"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["nutrition"]["nutrition_score"] is not None
    assert 0 <= data["nutrition"]["nutrition_score"] <= 100


# ─── Freshness ─────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_freshness_analyze_demo(client):
    from PIL import Image
    import io
    img = Image.new("RGB", (100, 100), color=(50, 180, 50))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    r = await client.post(
        "/api/v1/freshness/analyze",
        files={"file": ("apple.png", buf, "image/png")},
        data={"food_category": "Apple"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] in ("Fresh", "Moderately Fresh", "Possible Spoilage")
    assert "safety_disclaimer" in data
    assert data["metadata"]["is_demo"] is True


@pytest.mark.anyio
async def test_freshness_safety_disclaimer_present(client):
    from PIL import Image
    import io
    img = Image.new("RGB", (80, 80), color=(100, 180, 30))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    r = await client.post(
        "/api/v1/freshness/analyze",
        files={"file": ("veg.jpg", buf, "image/jpeg")},
        data={"food_category": "Vegetables"},
    )
    assert r.status_code == 200
    assert "cannot detect pathogens" in r.json()["safety_disclaimer"].lower() or "pathogens" in r.json()["safety_disclaimer"]


# ─── Hygiene ───────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_hygiene_analyze_demo(client):
    """Hygiene endpoint should return a demo report for any video in demo mode."""
    import io
    # Create minimal MP4 bytes (not a valid video, but tests the demo path)
    fake_video = io.BytesIO(b"\x00" * 1024)
    r = await client.post(
        "/api/v1/hygiene/analyze",
        files={"file": ("kitchen.mp4", fake_video, "video/mp4")},
    )
    assert r.status_code == 200
    data = r.json()
    assert "indicators" in data
    assert data["metadata"]["is_demo"] is True
    assert "disclaimer" in data


# ─── Cooking ───────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_cooking_generate_demo(client):
    r = await client.post(
        "/api/v1/cooking/generate",
        json={"dish_name": "Pasta Carbonara", "servings": 2, "difficulty": "medium"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "title" in data
    assert len(data["steps"]) > 0
    assert data["is_demo"] is True


@pytest.mark.anyio
async def test_cooking_chat_demo(client):
    r = await client.post(
        "/api/v1/cooking/chat",
        json={"recipe_id": "abc123", "message": "Can I make this vegetarian?"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "message" in data
    assert data["is_demo"] is True


# ─── Meal Plans ────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_meal_plan_generate_demo(client):
    r = await client.post(
        "/api/v1/meal-plans/generate",
        json={
            "dietary_pattern": "omnivore",
            "allergies": [],
            "excluded_foods": [],
            "meals_per_day": 3,
            "plan_days": 3,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert "plan_id" in data
    assert len(data["days"]) == 3
    assert data["is_demo"] is True


@pytest.mark.anyio
async def test_meal_plan_exclusion_handling(client):
    """Excluded foods should not appear in generated meals."""
    r = await client.post(
        "/api/v1/meal-plans/generate",
        json={
            "dietary_pattern": "omnivore",
            "allergies": [],
            "excluded_foods": ["salmon", "fish"],
            "meals_per_day": 3,
            "plan_days": 3,
        },
    )
    assert r.status_code == 200
    data = r.json()
    # Check no meal mentions salmon in ingredients
    for day in data["days"]:
        for meal in day["meals"]:
            for ing in meal.get("ingredients", []):
                assert "salmon" not in ing.lower()


@pytest.mark.anyio
async def test_meal_plan_list(client):
    # First generate a plan
    await client.post(
        "/api/v1/meal-plans/generate",
        json={"dietary_pattern": "vegetarian", "meals_per_day": 3, "plan_days": 3},
    )
    r = await client.get("/api/v1/meal-plans/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ─── History ───────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_history_list(client):
    r = await client.get("/api/v1/history/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.anyio
async def test_history_not_found(client):
    r = await client.get("/api/v1/history/nonexistent-id")
    assert r.status_code == 404


@pytest.mark.anyio
async def test_history_delete_not_found(client):
    r = await client.delete("/api/v1/history/nonexistent-id")
    assert r.status_code == 404


@pytest.mark.anyio
async def test_history_created_after_analysis(client):
    r = await client.post(
        "/api/v1/nutrition/analyze",
        json={"food_name": "Avocado Toast"},
    )
    assert r.status_code == 200
    analysis_id = r.json()["metadata"]["analysis_id"]
    rh = await client.get(f"/api/v1/history/{analysis_id}")
    assert rh.status_code == 200
    assert rh.json()["analysis_id"] == analysis_id
