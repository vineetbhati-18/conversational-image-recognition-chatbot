import os
from pathlib import Path
from uuid import uuid4
import aiofiles
from PIL import Image
import io
import logging
from app.core.exceptions import ImageProcessingError
from app.config import get_settings

logger = logging.getLogger("bel_chatbot.image_service")
settings = get_settings()

# Allowed MIME types and their magic signatures
MAGIC_SIGNATURES = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/webp": [b"RIFF"],
}

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


def detect_mime_from_magic_bytes(header: bytes) -> str:
    """
    Inspect raw binary header bytes to reliably verify actual image type.
    """
    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    elif header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    elif len(header) >= 12 and header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "image/webp"
    return "application/octet-stream"


async def validate_and_save_image(
    file_bytes: bytes,
    original_filename: str,
) -> dict:
    """
    Validates file size, magic bytes signature, and Pillow readability,
    then saves to local storage with a secure UUID.
    """
    # 1. Size Validation
    file_size = len(file_bytes)
    if file_size > MAX_FILE_BYTES:
        raise ImageProcessingError(
            f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB.",
            details={"file_size_bytes": file_size, "max_allowed_bytes": MAX_FILE_BYTES},
        )
    if file_size == 0:
        raise ImageProcessingError("Empty file uploaded.")

    # 2. Magic byte inspection
    header = file_bytes[:16]
    detected_mime = detect_mime_from_magic_bytes(header)
    if detected_mime not in MAGIC_SIGNATURES:
        raise ImageProcessingError(
            f"Invalid or unsafe image format. Detected: {detected_mime}. Allowed: JPEG, PNG, WebP.",
            details={"detected_mime": detected_mime},
        )

    # 3. Pillow Integrity Check & Dimension Extraction
    try:
        with Image.open(io.BytesIO(file_bytes)) as pil_img:
            pil_img.verify()

        # Re-open after verify() to read dimensions
        with Image.open(io.BytesIO(file_bytes)) as pil_img:
            width, height = pil_img.size
            format_name = pil_img.format
            # Downscale images to max 800px to strictly protect 512MB container memory
            if width > 800 or height > 800:
                img_copy = pil_img.copy()
                img_copy.thumbnail((800, 800), Image.Resampling.BILINEAR)
                buf = io.BytesIO()
                save_fmt = format_name if format_name in ("JPEG", "PNG", "WEBP") else "JPEG"
                img_copy.save(buf, format=save_fmt, quality=85)
                file_bytes = buf.getvalue()
                width, height = img_copy.size
                file_size = len(file_bytes)
                del img_copy
                buf.close()
    except Exception as e:
        raise ImageProcessingError(
            f"Corrupted or invalid image data: {str(e)}",
            details={"original_filename": original_filename},
        )

    # 4. Secure File Persistence
    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".jpg" if detected_mime == "image/jpeg" else ".png" if detected_mime == "image/png" else ".webp"

    image_id = uuid4()
    secure_filename = f"{image_id}{ext}"
    storage_path = settings.UPLOAD_DIR / secure_filename

    async with aiofiles.open(storage_path, "wb") as f:
        await f.write(file_bytes)

    logger.info(f"Persisted image {image_id} ({width}x{height}, {file_size} bytes) at {storage_path}")

    return {
        "id": image_id,
        "filename": original_filename,
        "secure_filename": secure_filename,
        "storage_path": str(storage_path),
        "url": f"/uploads/{secure_filename}",
        "width": width,
        "height": height,
        "file_size_bytes": file_size,
        "mime_type": detected_mime,
        "format": format_name,
    }
