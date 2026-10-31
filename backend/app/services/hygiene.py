"""Restaurant hygiene monitoring service supporting both image and video media."""
from __future__ import annotations
import uuid
import json
from datetime import datetime, timezone
from app.services.ai_provider import (
    AIProvider, DemoProvider, AIProviderError, AIResponseFormatError
)
from app.services.video_processor import extract_frames, get_video_duration
from app.schemas.schemas import HygieneReport, HygieneIndicator, AnalysisMetadata
from app.core.logging import get_logger

logger = get_logger(__name__)

HYGIENE_DISCLAIMER = (
    "IMPORTANT: These observations are based on preliminary visual analysis only. "
    "The absence of a visible indicator does not confirm noncompliance, and its presence does not certify "
    "compliance with food-safety regulations. Proper hygiene audits require trained inspectors following "
    "established protocols. This tool is not a substitute for official food-safety inspections."
)

DEMO_REPORT = {
    "overall_assessment": "Sample Hygiene Observation Report (Demo Mode)",
    "indicators": [
        {"indicator": "Hair restraints", "status": "observed", "evidence": "Staff visible with hair nets in food preparation area", "timestamp_seconds": 12.5},
        {"indicator": "Glove use", "status": "observed", "evidence": "Gloves worn during food handling tasks", "timestamp_seconds": 28.0},
        {"indicator": "Handwashing", "status": "unable_to_assess", "evidence": "Handwashing station not visible in analyzed media", "timestamp_seconds": None},
        {"indicator": "Food-contact surface cleanliness", "status": "observed", "evidence": "Preparation surfaces appear clean and organized", "timestamp_seconds": 35.0},
        {"indicator": "Raw/ready-to-eat food separation", "status": "unable_to_assess", "evidence": "Separation practices not clearly visible in this view", "timestamp_seconds": None},
        {"indicator": "Safe food handling practices", "status": "observed", "evidence": "Appropriate handling techniques observed in visible area", "timestamp_seconds": 45.0},
    ],
    "limitations": [
        "This is a demo report — no real media was analyzed.",
        "Camera angle limits visibility of several work areas.",
        "Handwashing stations and storage areas not in frame.",
    ],
    "corrective_actions": [
        "Ensure handwashing station is accessible and used regularly.",
        "Maintain documentation of temperature controls and cleaning schedules.",
        "Conduct regular in-person hygiene audits with qualified personnel.",
    ],
}


async def analyze_hygiene(
    media_path: str,
    provider: AIProvider,
    media_type: str = "video",
) -> HygieneReport:
    """Analyze restaurant hygiene from an image or video."""
    analysis_id = uuid.uuid4().hex
    is_demo = isinstance(provider, DemoProvider)
    duration = get_video_duration(media_path) if media_type == "video" else None

    if is_demo:
        warnings = [
            "DEMO MODE: No real media analysis was performed.",
            "This is a sample report for demonstration purposes only.",
            HYGIENE_DISCLAIMER,
        ]
        return HygieneReport(
            overall_assessment=f"{DEMO_REPORT['overall_assessment']} ({media_type.capitalize()} Input)",
            frames_analyzed=1 if media_type == "image" else 8,
            duration_seconds=duration or (60.0 if media_type == "video" else None),
            indicators=[HygieneIndicator(**i) for i in DEMO_REPORT["indicators"]],
            limitations=DEMO_REPORT["limitations"],
            corrective_actions=DEMO_REPORT["corrective_actions"],
            disclaimer=HYGIENE_DISCLAIMER,
            metadata=AnalysisMetadata(
                analysis_id=analysis_id,
                input_type=media_type,
                analysis_type="hygiene",
                provider="demo",
                is_demo=True,
                warnings=warnings,
                created_at=datetime.now(timezone.utc),
            ),
        )

    # Real provider path
    prompt = (
        "Analyze this image/frame from a restaurant kitchen or food service area. "
        "Identify visible hygiene indicators: hair restraints, glove use, handwashing evidence, "
        "surface cleanliness, food separation, safe handling practices. "
        "Return a JSON object: {\"observations\": [{\"indicator\": \"Hair restraints\", \"status\": \"observed\"|\"not_observed\"|\"unable_to_assess\", \"evidence\": \"description\"}]}. "
        "Only report what is actually visible. Do not infer from absence."
    )

    if media_type == "image":
        # Direct single-frame image analysis
        try:
            raw = await provider.analyze_image(media_path, prompt)
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start == -1 or end <= start:
                raise AIResponseFormatError("AI vision provider did not return valid JSON for hygiene analysis.")
            data = json.loads(raw[start:end])
            obs_list = data.get("observations", [])
            indicators = [
                HygieneIndicator(
                    indicator=o.get("indicator", "General hygiene"),
                    status=o.get("status", "unable_to_assess"),
                    evidence=o.get("evidence", ""),
                )
                for o in obs_list if isinstance(o, dict)
            ]
            return HygieneReport(
                overall_assessment="Hygiene observation report based on uploaded kitchen image.",
                frames_analyzed=1,
                duration_seconds=None,
                indicators=indicators,
                limitations=[
                    "Analysis based on a single static image.",
                    "Camera angle limits visibility of hidden areas.",
                    "Absence of observation does not indicate noncompliance.",
                ],
                corrective_actions=[
                    "Commission a full in-person hygiene audit for regulatory compliance assessment.",
                ],
                disclaimer=HYGIENE_DISCLAIMER,
                metadata=AnalysisMetadata(
                    analysis_id=analysis_id,
                    input_type="image",
                    analysis_type="hygiene",
                    provider=provider.name,
                    is_demo=False,
                    warnings=["Preliminary visual assessment only.", HYGIENE_DISCLAIMER],
                    created_at=datetime.now(timezone.utc),
                ),
            )
        except AIProviderError:
            raise
        except json.JSONDecodeError as exc:
            logger.error(f"Failed to parse hygiene JSON: {exc}")
            raise AIResponseFormatError("AI hygiene response contained invalid JSON.") from exc
        except Exception as e:
            logger.error(f"Image hygiene analysis failed: {e}")
            raise

    # Video path
    frames = extract_frames(media_path, max_frames=8)
    if not frames:
        logger.warning("No frames extracted from video")
        return HygieneReport(
            overall_assessment="Video frame extraction unavailable",
            frames_analyzed=0,
            duration_seconds=duration,
            indicators=[],
            limitations=[
                "Video frame extraction requires OpenCV (cv2), which is not installed in the environment.",
                "To analyze restaurant hygiene, upload a photo of the kitchen or install opencv-python.",
            ],
            corrective_actions=[
                "Upload a kitchen photo for direct single-frame AI analysis.",
            ],
            disclaimer=HYGIENE_DISCLAIMER,
            metadata=AnalysisMetadata(
                analysis_id=analysis_id,
                input_type="video",
                analysis_type="hygiene",
                provider=provider.name,
                is_demo=False,
                warnings=["Video frame extraction failed. Upload an image instead."],
                created_at=datetime.now(timezone.utc),
            ),
        )

    all_observations: list[dict] = []
    for frame_path in frames:
        try:
            raw = await provider.analyze_image(frame_path, prompt)
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(raw[start:end])
                all_observations.extend(data.get("observations", []))
        except AIProviderError:
            raise
        except Exception as e:
            logger.warning(f"Frame analysis failed for {frame_path}: {e}")

    # Deduplicate indicators
    seen = {}
    for obs in all_observations:
        if isinstance(obs, dict):
            key = obs.get("indicator", "")
            if key and key not in seen:
                seen[key] = obs

    indicators = [
        HygieneIndicator(
            indicator=v.get("indicator", ""),
            status=v.get("status", "unable_to_assess"),
            evidence=v.get("evidence", ""),
        )
        for v in seen.values()
    ]

    return HygieneReport(
        overall_assessment=f"Hygiene observation report based on {len(frames)} analyzed frames.",
        frames_analyzed=len(frames),
        duration_seconds=duration,
        indicators=indicators,
        limitations=[
            f"Only {len(frames)} frames analyzed out of the full video.",
            "Camera angles may limit visibility.",
            "Absence of observation ≠ noncompliance.",
        ],
        corrective_actions=[
            "Commission a full in-person hygiene audit for compliance assessment.",
        ],
        disclaimer=HYGIENE_DISCLAIMER,
        metadata=AnalysisMetadata(
            analysis_id=analysis_id,
            input_type="video",
            analysis_type="hygiene",
            provider=provider.name,
            is_demo=False,
            warnings=["Preliminary visual assessment only.", HYGIENE_DISCLAIMER],
            created_at=datetime.now(timezone.utc),
        ),
    )


async def analyze_hygiene_text(
    text: str,
    provider: AIProvider,
) -> HygieneReport:
    """Analyze restaurant hygiene indicators from a text description."""
    from fastapi import HTTPException
    analysis_id = uuid.uuid4().hex
    is_demo = isinstance(provider, DemoProvider)

    if is_demo:
        warnings = [
            "DEMO MODE: No real media analysis was performed.",
            "This is a sample report for demonstration purposes only.",
            HYGIENE_DISCLAIMER,
        ]
        return HygieneReport(
            overall_assessment=f"{DEMO_REPORT['overall_assessment']} (Text Input)",
            frames_analyzed=0,
            duration_seconds=None,
            indicators=[HygieneIndicator(**i) for i in DEMO_REPORT["indicators"]],
            limitations=[
                "This is a demo report — no real media or text was analyzed.",
                "Assessment based on demonstration data.",
            ],
            corrective_actions=DEMO_REPORT["corrective_actions"],
            disclaimer=HYGIENE_DISCLAIMER,
            metadata=AnalysisMetadata(
                analysis_id=analysis_id,
                input_type="text",
                analysis_type="hygiene",
                provider="demo",
                is_demo=True,
                warnings=warnings,
                created_at=datetime.now(timezone.utc),
            ),
        )

    prompt = (
        f"Analyze this description of a restaurant kitchen or food service area: \"{text}\". "
        "Identify visible/reported hygiene indicators: hair restraints, glove use, handwashing, "
        "surface cleanliness, raw/ready-to-eat food separation, safe food handling practices. "
        "Return a JSON object: {\"observations\": [{\"indicator\": \"Hair restraints\", \"status\": \"observed\"|\"not_observed\"|\"unable_to_assess\", \"evidence\": \"description\"}]}. "
        "Only report what is described. Do not infer without evidence."
    )
    system = "You are FoodVerse AI, a restaurant food safety and hygiene auditor. Analyze hygiene observations objectively."
    try:
        raw = await provider.generate_text(prompt, system=system)
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end <= start:
            raise AIResponseFormatError("AI provider did not return valid JSON for hygiene analysis.")
        data = json.loads(raw[start:end])
        obs_list = data.get("observations", [])
        indicators = [
            HygieneIndicator(
                indicator=o.get("indicator", "General hygiene"),
                status=o.get("status", "unable_to_assess"),
                evidence=o.get("evidence", ""),
            )
            for o in obs_list if isinstance(o, dict)
        ]
        return HygieneReport(
            overall_assessment="Hygiene observation report based on provided text description.",
            frames_analyzed=0,
            duration_seconds=None,
            indicators=indicators,
            limitations=[
                "Analysis based solely on text description.",
                "Observations cannot be independently verified from text alone.",
                "Absence of mention does not confirm compliance.",
            ],
            corrective_actions=[
                "Commission a certified in-person food safety inspection for regulatory compliance.",
            ],
            disclaimer=HYGIENE_DISCLAIMER,
            metadata=AnalysisMetadata(
                analysis_id=analysis_id,
                input_type="text",
                analysis_type="hygiene",
                provider=provider.name,
                is_demo=False,
                warnings=["Preliminary assessment based on text report.", HYGIENE_DISCLAIMER],
                created_at=datetime.now(timezone.utc),
            ),
        )
    except (AIProviderError, HTTPException):
        raise
    except json.JSONDecodeError as exc:
        logger.error(f"Failed to parse hygiene JSON: {exc}")
        raise AIResponseFormatError("AI hygiene response contained invalid JSON.") from exc
    except Exception as e:
        logger.error(f"Text hygiene analysis failed: {e}")
        raise
