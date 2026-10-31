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


@pytest.mark.anyio
async def test_history_delete_success(client):
    r = await client.post(
        "/api/v1/nutrition/analyze",
        json={"food_name": "Blueberry Oatmeal"},
    )
    assert r.status_code == 200
    analysis_id = r.json()["metadata"]["analysis_id"]

    del_res = await client.delete(f"/api/v1/history/{analysis_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"

    # Confirm it is gone
    check_res = await client.get(f"/api/v1/history/{analysis_id}")
    assert check_res.status_code == 404


# ─── Hygiene Multi-Media Support ──────────────────────────────────────────

@pytest.mark.anyio
async def test_hygiene_analyze_image_demo(client):
    from PIL import Image
    import io
    img = Image.new("RGB", (100, 100), color=(120, 120, 120))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    r = await client.post(
        "/api/v1/hygiene/analyze",
        files={"file": ("kitchen.jpg", buf, "image/jpeg")},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["metadata"]["input_type"] == "image"
    assert data["metadata"]["is_demo"] is True
    assert "indicators" in data


@pytest.mark.anyio
async def test_hygiene_invalid_media_type(client):
    import io
    fake_doc = io.BytesIO(b"Hygiene report PDF content")
    r = await client.post(
        "/api/v1/hygiene/analyze",
        files={"file": ("report.pdf", fake_doc, "application/pdf")},
    )
    assert r.status_code == 415


# ─── File Upload Validation & Limits ──────────────────────────────────────

@pytest.mark.anyio
async def test_image_upload_oversized(client, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "max_image_size_mb", 1)
    # Generate 1.5MB file
    import io
    fake_big_img = io.BytesIO(b"\xff\xd8\xff" + b"\x00" * int(1.5 * 1024 * 1024))
    r = await client.post(
        "/api/v1/food/recognize",
        files={"file": ("large.jpg", fake_big_img, "image/jpeg")},
    )
    assert r.status_code == 413
    assert "exceeds" in r.json()["detail"].lower()


# ─── Validation of Invalid Payloads ───────────────────────────────────────

@pytest.mark.anyio
async def test_cooking_missing_dish_name(client):
    r = await client.post("/api/v1/cooking/generate", json={"dish_name": ""})
    assert r.status_code == 422


@pytest.mark.anyio
async def test_meal_plan_invalid_days(client):
    r = await client.post(
        "/api/v1/meal-plans/generate",
        json={"dietary_pattern": "vegan", "meals_per_day": 3, "plan_days": 10},
    )
    assert r.status_code == 422


@pytest.mark.anyio
async def test_meal_plan_persisted_to_history(client):
    r = await client.post(
        "/api/v1/meal-plans/generate",
        json={"dietary_pattern": "omnivore", "meals_per_day": 3, "plan_days": 2},
    )
    assert r.status_code == 200
    plan_id = r.json()["plan_id"]
    # Check history
    rh = await client.get(f"/api/v1/history/{plan_id}")
    assert rh.status_code == 200
    assert rh.json()["analysis_type"] == "meal_plan"


# ─── Health Provider Status Tests ──────────────────────────────────────────

@pytest.mark.anyio
async def test_provider_status_demo(client):
    r = await client.get("/api/health/provider")
    assert r.status_code == 200
    data = r.json()
    assert data["mode"] == "demo"
    assert data["provider"] == "demo"
    assert data["reachable"] is False


@pytest.mark.anyio
async def test_provider_status_unconfigured_openai(client, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "ai_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "")
    r = await client.get("/api/health/provider")
    assert r.status_code == 200
    data = r.json()
    assert data["mode"] == "demo"
    assert data["configured"] is False


# ─── AI Provider Graceful Failure Handling ─────────────────────────────────

@pytest.mark.anyio
async def test_live_provider_failure_handling(client, monkeypatch):
    """When OpenAI call fails, endpoint returns 502 with sanitized message and no key leak."""
    from app.core.config import settings
    from unittest.mock import AsyncMock, patch

    monkeypatch.setattr(settings, "ai_provider", "openai")
    secret_key = "sk-testsecretkey123456789012345"
    monkeypatch.setattr(settings, "openai_api_key", secret_key)

    with patch("openai.resources.chat.completions.AsyncCompletions.create", new_callable=AsyncMock) as mock_create:
        import httpx
        request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
        response = httpx.Response(401, request=request)
        import openai
        mock_create.side_effect = openai.AuthenticationError(
            f"Invalid API key {secret_key}",
            response=response,
            body={"error": {"message": f"Invalid key {secret_key}"}},
        )

        r = await client.post(
            "/api/v1/nutrition/analyze",
            json={"food_name": "Tofu Bowl"},
        )
        assert r.status_code in (502, 503)
        detail = r.json().get("detail", "")
        # Critical verification: the secret key must never be leaked
        assert secret_key not in detail
        assert "authentication" in detail.lower() or "invalid" in detail.lower()


# ─── Gemini Provider Tests ────────────────────────────────────────────────

@pytest.mark.anyio
async def test_provider_status_unconfigured_gemini(client, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "")
    r = await client.get("/api/health/provider")
    assert r.status_code == 200
    data = r.json()
    assert data["provider"] == "gemini"
    assert data["configured"] is False
    assert data["reachable"] is False
    assert data["mode"] == "demo"


@pytest.mark.anyio
async def test_provider_status_live_gemini(client, monkeypatch):
    from app.core.config import settings
    from unittest.mock import AsyncMock, patch, MagicMock

    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "AIzaSyTestValidKey123456789012345")

    with patch("google.genai.models.AsyncModels.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = MagicMock(name="gemini-2.5-flash")
        r = await client.get("/api/health/provider")
        assert r.status_code == 200
        data = r.json()
        assert data["provider"] == "gemini"
        assert data["configured"] is True
        assert data["reachable"] is True
        assert data["mode"] == "live"
        assert data["model"] == settings.gemini_model


@pytest.mark.anyio
async def test_provider_status_degraded_gemini(client, monkeypatch):
    from app.core.config import settings
    from unittest.mock import AsyncMock, patch

    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "AIzaSyTestInvalidKey12345678901234")

    with patch("google.genai.models.AsyncModels.get", new_callable=AsyncMock) as mock_get:
        from google.genai import errors
        mock_get.side_effect = errors.ClientError(403, {"error": {"message": "Forbidden"}})
        r = await client.get("/api/health/provider")
        assert r.status_code == 200
        data = r.json()
        assert data["provider"] == "gemini"
        assert data["configured"] is True
        assert data["reachable"] is False
        assert data["mode"] == "degraded"


@pytest.mark.anyio
async def test_gemini_unconfigured_key_no_silent_fallback(client, monkeypatch):
    """When Gemini is selected but key is missing, raise auth error instead of silent fallback."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "")

    r = await client.post(
        "/api/v1/nutrition/analyze",
        json={"food_name": "Poke Bowl"},
    )
    assert r.status_code == 502
    data = r.json()
    assert data["code"] == "authentication_error"
    assert "GEMINI_API_KEY is not configured" in data["detail"]


@pytest.mark.anyio
async def test_gemini_food_recognition_image_live(client, monkeypatch):
    from app.core.config import settings
    from unittest.mock import AsyncMock, patch, MagicMock
    import json
    from PIL import Image
    import io

    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "AIzaSyTestKey1234567890123456789")

    mock_json = json.dumps({
        "dish_name": "Fresh Salmon Nigiri",
        "confidence": 0.94,
        "description": "Two pieces of fresh salmon sushi over seasoned rice.",
        "ingredients": [{"name": "Salmon", "confidence": 0.96}, {"name": "Rice", "confidence": 0.98}],
        "cuisine": "Japanese",
        "serving_size_estimate": "2 pieces (~120g)",
    })

    with patch("google.genai.models.AsyncModels.generate_content", new_callable=AsyncMock) as mock_gen:
        mock_resp = MagicMock()
        mock_resp.text = mock_json
        mock_gen.return_value = mock_resp

        img = Image.new("RGB", (60, 60), color=(220, 100, 80))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        r = await client.post(
            "/api/v1/food/recognize",
            files={"file": ("sushi.jpg", buf, "image/jpeg")},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["dish_name"] == "Fresh Salmon Nigiri"
        assert data["metadata"]["provider"] == "gemini"
        assert data["metadata"]["is_demo"] is False
        assert data["metadata"]["input_type"] == "image"


@pytest.mark.anyio
async def test_gemini_food_recognition_text_live(client, monkeypatch):
    from app.core.config import settings
    from unittest.mock import AsyncMock, patch, MagicMock
    import json

    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "AIzaSyTestKey1234567890123456789")

    mock_json = json.dumps({
        "dish_name": "Vegetable Pad Thai",
        "confidence": 0.91,
        "description": "Stir-fried rice noodles with tofu, peanuts, and bean sprouts.",
        "ingredients": [{"name": "Rice noodles", "confidence": 0.95}, {"name": "Tofu", "confidence": 0.92}],
        "cuisine": "Thai",
        "serving_size_estimate": "1 plate (~350g)",
    })

    with patch("google.genai.models.AsyncModels.generate_content", new_callable=AsyncMock) as mock_gen:
        mock_resp = MagicMock()
        mock_resp.text = mock_json
        mock_gen.return_value = mock_resp

        # Form text on /recognize
        r = await client.post(
            "/api/v1/food/recognize",
            data={"text": "A plate of Pad Thai with extra peanuts and lime"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["dish_name"] == "Vegetable Pad Thai"
        assert data["metadata"]["input_type"] == "text"
        assert data["metadata"]["provider"] == "gemini"

        # Dedicated JSON endpoint /recognize-text
        r2 = await client.post(
            "/api/v1/food/recognize-text",
            json={"text": "Pad Thai noodles with tofu"},
        )
        assert r2.status_code == 200
        assert r2.json()["dish_name"] == "Vegetable Pad Thai"


@pytest.mark.anyio
async def test_gemini_nutrition_analysis_text_and_image_live(client, monkeypatch):
    from app.core.config import settings
    from unittest.mock import AsyncMock, patch, MagicMock
    import json
    from PIL import Image
    import io

    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "AIzaSyTestKey1234567890123456789")

    mock_json = json.dumps({
        "food_name": "Avocado & Egg Toast",
        "calories": 360,
        "protein_g": 14,
        "carbs_g": 28,
        "fat_g": 22,
        "fiber_g": 7,
        "sugar_g": 2,
        "sodium_mg": 380,
    })

    with patch("google.genai.models.AsyncModels.generate_content", new_callable=AsyncMock) as mock_gen:
        mock_resp = MagicMock()
        mock_resp.text = mock_json
        mock_gen.return_value = mock_resp

        # Text nutrition
        r = await client.post(
            "/api/v1/nutrition/analyze",
            json={"food_name": "Avocado and poached egg toast", "serving_size": "2 slices"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["nutrition"]["calories"] == 360
        assert data["metadata"]["provider"] == "gemini"
        assert data["metadata"]["is_demo"] is False
        assert data["metadata"]["input_type"] == "text"

        # Image nutrition
        img = Image.new("RGB", (50, 50), color=(100, 200, 100))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        r_img = await client.post(
            "/api/v1/nutrition/analyze-image",
            files={"file": ("toast.png", buf, "image/png")},
            data={"serving_size": "2 slices"},
        )
        assert r_img.status_code == 200
        data_img = r_img.json()
        assert data_img["nutrition"]["calories"] == 360
        assert data_img["metadata"]["input_type"] == "image"
        assert data_img["metadata"]["provider"] == "gemini"


@pytest.mark.anyio
async def test_gemini_freshness_image_and_text_live(client, monkeypatch):
    from app.core.config import settings
    from unittest.mock import AsyncMock, patch, MagicMock
    import json
    from PIL import Image
    import io

    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "AIzaSyTestKey1234567890123456789")

    mock_json = json.dumps({
        "status": "Fresh",
        "confidence": 0.89,
        "observations": [
            {"characteristic": "Skin", "observation": "Bright red with no bruising", "severity": "normal"}
        ],
        "next_steps": ["Store in crisper drawer"],
    })

    with patch("google.genai.models.AsyncModels.generate_content", new_callable=AsyncMock) as mock_gen:
        mock_resp = MagicMock()
        mock_resp.text = mock_json
        mock_gen.return_value = mock_resp

        # Image freshness
        img = Image.new("RGB", (50, 50), color=(220, 20, 20))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        r = await client.post(
            "/api/v1/freshness/analyze",
            files={"file": ("apple.jpg", buf, "image/jpeg")},
            data={"food_category": "Apples"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "Fresh"
        assert data["metadata"]["provider"] == "gemini"
        assert data["metadata"]["input_type"] == "image"

        # Text freshness
        r_text = await client.post(
            "/api/v1/freshness/analyze-text",
            json={"text": "Strawberries are bright red and firm with green leaves", "food_category": "Berries"},
        )
        assert r_text.status_code == 200
        assert r_text.json()["metadata"]["input_type"] == "text"


@pytest.mark.anyio
async def test_gemini_hygiene_media_and_text_live(client, monkeypatch):
    from app.core.config import settings
    from unittest.mock import AsyncMock, patch, MagicMock
    import json
    from PIL import Image
    import io

    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "AIzaSyTestKey1234567890123456789")

    mock_json = json.dumps({
        "observations": [
            {"indicator": "Hair restraints", "status": "observed", "evidence": "Chef hats and hairnets visible"},
            {"indicator": "Glove use", "status": "observed", "evidence": "Disposable gloves worn during plating"},
        ]
    })

    with patch("google.genai.models.AsyncModels.generate_content", new_callable=AsyncMock) as mock_gen:
        mock_resp = MagicMock()
        mock_resp.text = mock_json
        mock_gen.return_value = mock_resp

        # Image hygiene
        img = Image.new("RGB", (60, 60), color=(180, 180, 180))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        r = await client.post(
            "/api/v1/hygiene/analyze",
            files={"file": ("kitchen.jpg", buf, "image/jpeg")},
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data["indicators"]) == 2
        assert data["metadata"]["provider"] == "gemini"
        assert data["metadata"]["input_type"] == "image"

        # Text hygiene
        r_text = await client.post(
            "/api/v1/hygiene/analyze-text",
            json={"text": "Prep staff wearing clean aprons, hairnets, and changing cutting boards between meats."},
        )
        assert r_text.status_code == 200
        assert r_text.json()["metadata"]["input_type"] == "text"


@pytest.mark.anyio
async def test_gemini_cooking_generate_and_chat_live(client, monkeypatch):
    from app.core.config import settings
    from unittest.mock import AsyncMock, patch, MagicMock
    import json

    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "AIzaSyTestKey1234567890123456789")

    recipe_json = json.dumps({
        "title": "Lemon Herb Baked Salmon",
        "description": "Quick weeknight salmon with fragrant fresh dill and lemon slices.",
        "cuisine": "Mediterranean",
        "dietary_info": "Pescatarian, Gluten-Free",
        "prep_time_minutes": 10,
        "cook_time_minutes": 15,
        "servings": 2,
        "difficulty": "easy",
        "ingredients": [{"item": "Salmon fillets", "quantity": "2", "unit": "fillets", "preparation": "patted dry"}],
        "steps": [{"step_number": 1, "instruction": "Bake at 200°C for 12-15 minutes.", "duration_minutes": 15, "tip": "Use a thermometer"}],
        "substitutions": ["Use trout instead of salmon"],
        "equipment": ["Baking sheet", "Parchment paper"],
        "allergen_notes": ["Contains fish"],
        "food_safety_notes": ["Cook salmon to 63°C internal temperature."],
    })

    with patch("google.genai.models.AsyncModels.generate_content", new_callable=AsyncMock) as mock_gen:
        mock_resp = MagicMock()
        mock_resp.text = recipe_json
        mock_gen.return_value = mock_resp

        r = await client.post(
            "/api/v1/cooking/generate",
            json={"dish_name": "Baked Salmon", "servings": 2},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["title"] == "Lemon Herb Baked Salmon"
        assert data["is_demo"] is False

        # Chat
        mock_resp.text = "You can substitute lime or orange slices if fresh lemons are not available."
        r_chat = await client.post(
            "/api/v1/cooking/chat",
            json={"recipe_id": data["recipe_id"], "message": "Can I use lime instead of lemon?"},
        )
        assert r_chat.status_code == 200
        assert r_chat.json()["is_demo"] is False
        assert "lime" in r_chat.json()["message"]


@pytest.mark.anyio
async def test_gemini_meal_plan_generate_live(client, monkeypatch):
    from app.core.config import settings
    from unittest.mock import AsyncMock, patch, MagicMock
    import json

    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "AIzaSyTestKey1234567890123456789")

    plan_json = json.dumps({
        "title": "Healthy Mediterranean Week",
        "days": [
            {
                "day": 1,
                "date_label": "Day 1",
                "meals": [
                    {"meal_type": "lunch", "name": "Greek Salad", "description": "Salad with feta", "ingredients": ["Feta", "Cucumber", "Tomato"], "serving_size": "1 bowl", "prep_time_minutes": 10, "estimated_calories": 350, "brief_instructions": "Toss together."}
                ],
                "daily_estimated_calories": 350,
            }
        ],
        "shopping_list": [{"ingredient": "Feta", "quantity": "200g", "category": "dairy"}],
    })

    with patch("google.genai.models.AsyncModels.generate_content", new_callable=AsyncMock) as mock_gen:
        mock_resp = MagicMock()
        mock_resp.text = plan_json
        mock_gen.return_value = mock_resp

        r = await client.post(
            "/api/v1/meal-plans/generate",
            json={"dietary_pattern": "mediterranean", "meals_per_day": 1, "plan_days": 1},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["is_demo"] is False
        assert data["title"] == "Healthy Mediterranean Week"
        assert len(data["days"]) == 1


@pytest.mark.anyio
async def test_gemini_rate_limit_error(client, monkeypatch):
    from app.core.config import settings
    from unittest.mock import AsyncMock, patch
    from google.genai import errors

    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "AIzaSyTestKeyRateLimit1234567890")

    with patch("google.genai.models.AsyncModels.generate_content", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = errors.APIError(429, {"error": {"message": "Resource has been exhausted", "status": "RESOURCE_EXHAUSTED"}})
        r = await client.post(
            "/api/v1/nutrition/analyze",
            json={"food_name": "Quinoa Salad"},
        )
        assert r.status_code == 502
        assert r.json()["code"] == "rate_limit_error"
        assert "quota exceeded" in r.json()["detail"].lower() or "rate limit" in r.json()["detail"].lower()


@pytest.mark.anyio
async def test_gemini_auth_error_sanitizes_key(client, monkeypatch):
    from app.core.config import settings
    from unittest.mock import AsyncMock, patch
    from google.genai import errors

    secret_key = "AIzaSySuperSecretKeyNotToBeLeaked"
    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", secret_key)

    with patch("google.genai.models.AsyncModels.generate_content", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = errors.APIError(400, {"error": {"message": f"API key not valid: {secret_key}"}})
        r = await client.post(
            "/api/v1/nutrition/analyze",
            json={"food_name": "Tofu Scramble"},
        )
        assert r.status_code == 502
        assert r.json()["code"] == "authentication_error"
        # Verify secret key was never returned in error detail
        assert secret_key not in r.json()["detail"]


@pytest.mark.anyio
async def test_gemini_timeout_error(client, monkeypatch):
    from app.core.config import settings
    from unittest.mock import AsyncMock, patch

    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "AIzaSyTestKeyTimeout1234567890")

    with patch("google.genai.models.AsyncModels.generate_content", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = TimeoutError("Request timed out after 30 seconds")
        r = await client.post(
            "/api/v1/nutrition/analyze",
            json={"food_name": "Vegetable Soup"},
        )
        assert r.status_code == 503
        assert r.json()["code"] == "connection_error"
        assert "timed out" in r.json()["detail"].lower()


@pytest.mark.anyio
@pytest.mark.anyio
async def test_gemini_timeout_configuration_and_conversion(monkeypatch):
    """Verify Gemini client sets timeout in milliseconds (>=60000ms) and has 10s connect timeout."""
    from app.core.config import settings
    from app.services.ai_provider import GeminiProvider
    from google.genai import _api_client
    import httpx

    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "AIzaSyTestKeyValid1234567890")
    monkeypatch.setattr(settings, "gemini_timeout_seconds", 90.0)
    monkeypatch.setattr(settings, "gemini_connect_timeout_seconds", 10.0)

    provider = GeminiProvider()
    client = provider._get_client()

    # The Google GenAI SDK expects milliseconds in HttpOptions.timeout
    http_options = client._api_client._http_options
    timeout_ms = http_options.timeout
    assert timeout_ms is not None
    assert timeout_ms >= 60000  # at least 60 seconds (60,000 ms)
    assert timeout_ms <= 120000  # within 60-120s range

    # Verify that the SDK's get_timeout_in_seconds accurately converts to seconds
    timeout_in_sec = _api_client.get_timeout_in_seconds(timeout_ms)
    assert timeout_in_sec == 90.0

    # Verify granular timeout on httpx client
    async_args = client._api_client._async_httpx_client_args
    assert "timeout" in async_args
    client_timeout = async_args["timeout"]
    assert isinstance(client_timeout, httpx.Timeout)
    assert client_timeout.connect == 10.0
    assert client_timeout.read == 90.0
    assert client_timeout.write == 90.0

    import asyncio
    del client
    del provider
    await asyncio.sleep(0.01)


@pytest.mark.anyio
async def test_gemini_food_recognition_image_sends_bytes_mime_and_timeout(client, monkeypatch):
    """Verify food recognition sends actual image bytes, correct MIME type, and sensible timeout to Gemini."""
    from app.core.config import settings
    from unittest.mock import AsyncMock, patch, MagicMock
    from PIL import Image
    import io
    import json

    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "AIzaSyTestKey1234567890123456789")

    mock_json = json.dumps({
        "dish_name": "Avocado Salad",
        "confidence": 0.95,
        "description": "Fresh avocado salad",
        "ingredients": [{"name": "Avocado", "confidence": 0.9}],
        "cuisine": "Mexican",
        "serving_size_estimate": "1 bowl",
    })

    with patch("google.genai.models.AsyncModels.generate_content", new_callable=AsyncMock) as mock_gen:
        mock_resp = MagicMock()
        mock_resp.text = mock_json
        mock_gen.return_value = mock_resp

        # Generate a distinct image with known bytes
        img = Image.new("RGB", (30, 30), color=(50, 150, 200))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        raw_bytes = buf.getvalue()
        buf.seek(0)

        r = await client.post(
            "/api/v1/food/recognize",
            files={"file": ("salad.jpg", buf, "image/jpeg")},
        )
        assert r.status_code == 200
        assert mock_gen.call_count == 1

        # Inspect kwargs passed to generate_content
        call_kwargs = mock_gen.call_args.kwargs
        contents = call_kwargs["contents"]
        image_part = contents[0]
        # Verify part has correct MIME type and matches uploaded image bytes
        assert image_part.inline_data.mime_type == "image/jpeg"
        assert image_part.inline_data.data == raw_bytes

        # Verify timeout is configured in milliseconds (>= 60,000 ms, not 30 ms / 0.03s!)
        config = call_kwargs["config"]
        timeout_ms = config.http_options.timeout
        assert timeout_ms is not None
        assert timeout_ms >= 60000
        assert timeout_ms <= 120000


@pytest.mark.anyio
async def test_gemini_write_timeout_exception_handling(client, monkeypatch):
    """When a WriteTimeout occurs during image upload, return 503 connection error without falling back to demo."""
    from app.core.config import settings
    from unittest.mock import AsyncMock, patch
    import httpcore
    from PIL import Image
    import io

    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "AIzaSyTestKeyTimeout1234567890")

    with patch("google.genai.models.AsyncModels.generate_content", new_callable=AsyncMock) as mock_gen:
        # Simulate the exact exception logged by httpcore during image send timeout
        mock_gen.side_effect = httpcore.WriteTimeout(TimeoutError())

        img = Image.new("RGB", (20, 20), color=(100, 100, 100))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        r = await client.post(
            "/api/v1/food/recognize",
            files={"file": ("test_dish.jpg", buf, "image/jpeg")},
        )
        assert r.status_code == 503
        data = r.json()
        assert data["code"] == "connection_error"
        assert "timed out" in data["detail"].lower()
        # Verify it did NOT silently fall back to demo data (e.g. "Grilled Chicken Salad")
        assert "dish_name" not in data


@pytest.mark.anyio
async def test_secret_redaction_utility():
    from app.services.ai_provider import redact_secrets
    raw = "Error with key AIzaSyABC12345678901234567890123456 and sk-abcdef123456789012345678"
    redacted = redact_secrets(raw)
    assert "AIzaSyABC12345678901234567890123456" not in redacted
    assert "sk-abcdef123456789012345678" not in redacted
    assert "[REDACTED_KEY]" in redacted


