"""Video processor for frame extraction."""
from __future__ import annotations
import uuid
from pathlib import Path
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def extract_frames(video_path: str, max_frames: int = 8) -> list[str]:
    """
    Extract up to max_frames frames from a video.
    Requires OpenCV. Falls back gracefully if not installed.
    Returns list of saved frame paths.
    """
    try:
        import cv2
    except ImportError:
        logger.warning("OpenCV not installed — cannot extract video frames.")
        return []

    frames = []
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Cannot open video: {video_path}")
        return []

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    duration = total_frames / fps if fps > 0 else 0

    if duration > settings.max_video_duration_seconds:
        logger.warning(f"Video duration {duration:.1f}s exceeds limit {settings.max_video_duration_seconds}s")
        # Still extract but from first N seconds only

    # Select frame indices evenly spaced
    step = max(1, total_frames // max_frames)
    frame_indices = list(range(0, min(total_frames, step * max_frames), step))[:max_frames]

    frame_dir = settings.resolved_upload_dir / "frames"
    frame_dir.mkdir(parents=True, exist_ok=True)

    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            frame_path = frame_dir / f"{uuid.uuid4().hex}.jpg"
            cv2.imwrite(str(frame_path), frame)
            frames.append(str(frame_path))

    cap.release()
    logger.info(f"Extracted {len(frames)} frames from {video_path}")
    return frames


def get_video_duration(video_path: str) -> float:
    """Return video duration in seconds, or 0 if OpenCV unavailable."""
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        cap.release()
        return frames / fps if fps > 0 else 0
    except ImportError:
        return 0
