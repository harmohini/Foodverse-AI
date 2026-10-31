"""File upload storage and validation utilities."""
from __future__ import annotations
import uuid
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/webm"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm"}
ALLOWED_AUDIO_TYPES = {"audio/wav", "audio/mpeg", "audio/mp4", "audio/x-m4a"}
ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a"}


def _safe_extension(filename: str) -> str:
    """Return the lowercase file extension."""
    return Path(filename).suffix.lower()


def _save_upload(upload: UploadFile, subdir: str) -> Path:
    """Save an upload to a safe path and return the path."""
    ext = _safe_extension(upload.filename or "file")
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest_dir = settings.resolved_upload_dir / subdir
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / safe_name
    with dest.open("wb") as f:
        shutil.copyfileobj(upload.file, f)
    logger.info(f"Saved upload to {dest}")
    return dest


async def validate_and_save_image(upload: UploadFile) -> Path:
    """Validate image file and save it. Returns the saved path."""
    if not upload.filename:
        raise HTTPException(status_code=422, detail="Filename is required.")
    ext = _safe_extension(upload.filename)
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported image format '{ext}'. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}",
        )
    # Check content-type header (advisory, not authoritative)
    content_type = upload.content_type or ""
    if content_type and content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported content type '{content_type}'.",
        )
    # Read first bytes for size check
    contents = await upload.read()
    if len(contents) > settings.max_image_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Image exceeds the {settings.max_image_size_mb} MB limit.",
        )
    # Validate image content with Pillow
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(contents))
        img.verify()
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid or corrupt image file: {e}")
    # Save
    ext2 = _safe_extension(upload.filename)
    safe_name = f"{uuid.uuid4().hex}{ext2}"
    dest_dir = settings.resolved_upload_dir / "images"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / safe_name
    dest.write_bytes(contents)
    return dest


async def validate_and_save_video(upload: UploadFile) -> Path:
    """Validate video file and save it. Returns the saved path."""
    if not upload.filename:
        raise HTTPException(status_code=422, detail="Filename is required.")
    ext = _safe_extension(upload.filename)
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported video format '{ext}'. Allowed: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}",
        )
    contents = await upload.read()
    if len(contents) > settings.max_video_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Video exceeds the {settings.max_video_size_mb} MB limit.",
        )
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest_dir = settings.resolved_upload_dir / "videos"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / safe_name
    dest.write_bytes(contents)
    return dest


async def validate_and_save_media(upload: UploadFile) -> tuple[Path, str]:
    """Validate and save either an image or video upload. Returns (saved_path, media_type)."""
    if not upload.filename:
        raise HTTPException(status_code=422, detail="Filename is required.")
    ext = _safe_extension(upload.filename)
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        p = await validate_and_save_image(upload)
        return p, "image"
    if ext in ALLOWED_VIDEO_EXTENSIONS:
        p = await validate_and_save_video(upload)
        return p, "video"
    allowed_all = ", ".join(sorted(ALLOWED_IMAGE_EXTENSIONS | ALLOWED_VIDEO_EXTENSIONS))
    raise HTTPException(
        status_code=415,
        detail=f"Unsupported media format '{ext}'. Supported formats: {allowed_all}",
    )


def delete_file(path: str) -> None:
    """Safely delete an uploaded file."""
    try:
        p = Path(path)
        if p.exists() and settings.resolved_upload_dir in p.parents:
            p.unlink()
            logger.info(f"Deleted file {p}")
    except Exception as e:
        logger.warning(f"Could not delete file {path}: {e}")
