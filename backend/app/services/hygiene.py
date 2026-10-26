"""Restaurant hygiene monitoring service."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from app.services.ai_provider import AIProvider, DemoProvider
from app.services.video_processor import extract_frames, get_video_duration
from app.schemas.schemas import HygieneReport, HygieneIndicator, AnalysisMetadata
from app.core.logging import get_logger

logger = get_logger(__name__)

HYGIENE_DISCLAIMER = (
    "IMPORTANT: These observations are based on preliminary visual analysis of selected video frames only. "
    "The absence of a visible indicator does not confirm noncompliance, and its presence does not certify "
    "compliance with food-safety regulations. Proper hygiene audits require trained inspectors following "
    "established protocols. This tool is not a substitute for official food-safety inspections."
)

DEMO_REPORT = {
    "overall_assessment": "Sample Hygiene Observation Report (Demo Mode)",
    "indicators": [
        {"indicator": "Hair restraints", "status": "observed", "evidence": "Staff visible with hair nets in food preparation area", "timestamp_seconds": 12.5},
        {"indicator": "Glove use", "status": "observed", "evidence": "Gloves worn during food handling tasks", "timestamp_seconds": 28.0},
        {"indicator": "Handwashing", "status": "unable_to_assess", "evidence": "Handwashing station not visible in analyzed frames", "timestamp_seconds": None},
        {"indicator": "Food-contact surface cleanliness", "status": "observed", "evidence": "Preparation surfaces appear clean and organized", "timestamp_seconds": 35.0},
        {"indicator": "Raw/ready-to-eat food separation", "status": "unable_to_assess", "evidence": "Separation practices not clearly visible in these frames", "timestamp_seconds": None},
        {"indicator": "Safe food handling practices", "status": "observed", "evidence": "Appropriate handling techniques observed in visible frames", "timestamp_seconds": 45.0},
    ],
    "limitations": [
        "Only 8 frames were analyzed from this video sample.",
        "Camera angle limits visibility of several work areas.",
        "Handwashing stations and storage areas not in frame.",
        "This is a demo report — no real video was analyzed.",
    ],
    "corrective_actions": [
        "Ensure handwashing station is accessible and used regularly.",
        "Maintain documentation of temperature controls and cleaning schedules.",
        "Conduct regular in-person hygiene audits with qualified personnel.",
    ],
}


async def analyze_hygiene(
    video_path: str,
    provider: AIProvider,
) -> HygieneReport:
    """Analyze restaurant hygiene from a video."""
    analysis_id = uuid.uuid4().hex
    is_demo = isinstance(provider, DemoProvider)
    duration = get_video_duration(video_path)

    if is_demo:
        warnings = [
            "DEMO MODE: No real video analysis was performed.",
            "This is a sample report for demonstration purposes only.",
            HYGIENE_DISCLAIMER,
        ]
        return HygieneReport(
            overall_assessment=DEMO_REPORT["overall_assessment"],
            frames_analyzed=8,
            duration_seconds=duration or 60.0,
            indicators=[HygieneIndicator(**i) for i in DEMO_REPORT["indicators"]],
            limitations=DEMO_REPORT["limitations"],
            corrective_actions=DEMO_REPORT["corrective_actions"],
            disclaimer=HYGIENE_DISCLAIMER,
            metadata=AnalysisMetadata(
                analysis_id=analysis_id,
                input_type="video",
                analysis_type="hygiene",
                provider="demo",
                is_demo=True,
                warnings=warnings,
                created_at=datetime.now(timezone.utc),
            ),
        )

    # Real provider path — extract frames and analyze each
    frames = extract_frames(video_path, max_frames=8)
    if not frames:
        # Fall back to demo report if frame extraction unavailable
        logger.warning("No frames extracted — returning limited demo report")
        return HygieneReport(
            overall_assessment="Unable to extract video frames for analysis",
            frames_analyzed=0,
            duration_seconds=duration,
            indicators=[],
            limitations=["Video frame extraction failed. Install OpenCV for video analysis."],
            corrective_actions=[],
            disclaimer=HYGIENE_DISCLAIMER,
            metadata=AnalysisMetadata(
                analysis_id=analysis_id,
                input_type="video",
                analysis_type="hygiene",
                provider=provider.name,
                is_demo=False,
                warnings=["Frame extraction failed."],
                created_at=datetime.now(timezone.utc),
            ),
        )

    prompt = (
        "Analyze this video frame from a restaurant kitchen or food service area. "
        "Identify hygiene indicators: hair restraints, glove use, handwashing evidence, "
        "surface cleanliness, food separation, safe handling practices. "
        "Return JSON: {observations: [{indicator, status: 'observed'|'not_observed'|'unable_to_assess', evidence}]}. "
        "Only report what is actually visible. Do not infer from absence."
    )

    all_observations: list[dict] = []
    for frame_path in frames:
        try:
            raw = await provider.analyze_image(frame_path, prompt)
            import json
            start = raw.find("{")
            end = raw.rfind("}") + 1
            data = json.loads(raw[start:end])
            all_observations.extend(data.get("observations", []))
        except Exception as e:
            logger.warning(f"Frame analysis failed for {frame_path}: {e}")

    # Deduplicate indicators
    seen = {}
    for obs in all_observations:
        key = obs.get("indicator", "")
        if key not in seen:
            seen[key] = obs

    indicators = [HygieneIndicator(
        indicator=v.get("indicator", ""),
        status=v.get("status", "unable_to_assess"),
        evidence=v.get("evidence", ""),
    ) for v in seen.values()]

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
