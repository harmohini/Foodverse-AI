"""Freshness detection service."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from app.services.ai_provider import AIProvider, DemoProvider
from app.schemas.schemas import FreshnessResult, FreshnessObservation, AnalysisMetadata
from app.core.logging import get_logger

logger = get_logger(__name__)

SAFETY_DISCLAIMER = (
    "IMPORTANT: This is a preliminary visual assessment only. It cannot detect pathogens, internal "
    "contamination, temperature abuse, or off-flavors. Smell, texture, storage history, and proper "
    "temperature control are critical indicators that cannot be assessed from an image. "
    "When in doubt, discard the food. Never rely solely on AI image analysis for food safety decisions."
)

DEMO_RESULTS = {
    "fresh": {
        "status": "Fresh",
        "confidence": 0.82,
        "observations": [
            {"characteristic": "Color", "observation": "Vibrant, natural coloration consistent with fresh produce", "severity": "normal"},
            {"characteristic": "Surface texture", "observation": "Smooth surface without visible blemishes or soft spots", "severity": "normal"},
            {"characteristic": "Visible moisture", "observation": "Appropriate moisture level; no signs of excessive drying", "severity": "normal"},
        ],
        "next_steps": [
            "Store properly according to food-safety guidelines.",
            "Consume within the expected shelf life for this food type.",
            "Continue to monitor for changes in smell, texture, or appearance.",
        ],
    },
    "moderate": {
        "status": "Moderately Fresh",
        "confidence": 0.71,
        "observations": [
            {"characteristic": "Color", "observation": "Slight color variation visible; may indicate early aging", "severity": "mild"},
            {"characteristic": "Surface texture", "observation": "Minor surface softening observed in some areas", "severity": "mild"},
            {"characteristic": "Visible spots", "observation": "Small blemish or darkened area noted", "severity": "mild"},
        ],
        "next_steps": [
            "Use soon — ideally within 1–2 days.",
            "Remove any clearly affected areas before preparation.",
            "Check smell and texture before eating.",
            "When uncertain, prioritize food safety over avoiding waste.",
        ],
    },
    "spoilage": {
        "status": "Possible Spoilage",
        "confidence": 0.68,
        "observations": [
            {"characteristic": "Color", "observation": "Significant discoloration or browning observed", "severity": "concerning"},
            {"characteristic": "Surface texture", "observation": "Visible soft spots, wrinkling, or surface breakdown", "severity": "concerning"},
            {"characteristic": "Surface changes", "observation": "Possible mold, sliminess, or bruising visible", "severity": "concerning"},
        ],
        "next_steps": [
            "Exercise caution — the visual indicators suggest possible spoilage.",
            "Check smell carefully; off-odors are a strong spoilage indicator.",
            "If there is any doubt, discard the food — the risk is not worth it.",
            "Never taste food to test if it is safe.",
            "Consult food-safety guidelines for your specific food type.",
        ],
    },
}


async def analyze_freshness(
    image_path: str,
    food_category: str,
    provider: AIProvider,
) -> FreshnessResult:
    """Analyze food freshness from an image."""
    analysis_id = uuid.uuid4().hex
    is_demo = isinstance(provider, DemoProvider)

    if is_demo:
        # Use the "moderate" demo result to show all relevant fields
        demo = DEMO_RESULTS["moderate"]
        warnings = [
            "DEMO MODE: No real image analysis was performed.",
            "This is a sample result for demonstration purposes only.",
            SAFETY_DISCLAIMER,
        ]
        return FreshnessResult(
            food_category=food_category or "General produce",
            status=demo["status"],
            confidence=demo["confidence"],
            observations=[FreshnessObservation(**o) for o in demo["observations"]],
            next_steps=demo["next_steps"],
            safety_disclaimer=SAFETY_DISCLAIMER,
            metadata=AnalysisMetadata(
                analysis_id=analysis_id,
                input_type="image",
                analysis_type="freshness",
                provider="demo",
                is_demo=True,
                warnings=warnings,
                created_at=datetime.now(timezone.utc),
            ),
        )

    # Real provider path
    prompt = (
        f"Analyze this image of {food_category or 'food'} for freshness indicators. "
        "Return a JSON object with: status (one of 'Fresh', 'Moderately Fresh', 'Possible Spoilage'), "
        "confidence (0-1), observations (array of {characteristic, observation, severity: 'normal'|'mild'|'concerning'}), "
        "next_steps (array of strings). "
        "Be conservative and honest. If the image is insufficient, say so. "
        "Do not claim to detect pathogens or guarantee food safety."
    )
    try:
        raw = await provider.analyze_image(image_path, prompt)
        import json
        start = raw.find("{")
        end = raw.rfind("}") + 1
        data = json.loads(raw[start:end])
        return FreshnessResult(
            food_category=food_category or "Unknown",
            status=data.get("status", "Unable to assess"),
            confidence=data.get("confidence"),
            observations=[FreshnessObservation(**o) for o in data.get("observations", [])],
            next_steps=data.get("next_steps", []),
            safety_disclaimer=SAFETY_DISCLAIMER,
            metadata=AnalysisMetadata(
                analysis_id=analysis_id,
                input_type="image",
                analysis_type="freshness",
                provider=provider.name,
                is_demo=False,
                warnings=[
                    "Preliminary visual assessment only.",
                    SAFETY_DISCLAIMER,
                ],
                created_at=datetime.now(timezone.utc),
            ),
        )
    except Exception as e:
        logger.error(f"Freshness analysis failed: {e}")
        raise
