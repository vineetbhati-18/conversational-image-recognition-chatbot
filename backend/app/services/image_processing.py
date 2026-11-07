import os
from pathlib import Path
from uuid import uuid4
from PIL import Image
import io
import logging
from app.core.exceptions import ImageProcessingError
from app.config import get_settings
from app.utils.memory import trim_process_memory

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
    Applies in-place streaming downscale to max 800px to protect 512MB RAM environments.
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

    # 3. Secure File Path Preparation
    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".jpg" if detected_mime == "image/jpeg" else ".png" if detected_mime == "image/png" else ".webp"

    image_id = uuid4()
    secure_filename = f"{image_id}{ext}"
    storage_path = settings.UPLOAD_DIR / secure_filename

    # 4. Streamlined In-Place Pillow Processing & Direct Disk Persistence
    try:
        bio = io.BytesIO(file_bytes)
        with Image.open(bio) as pil_img:
            # Handle orientation EXIF metadata if present
            try:
                from PIL import ImageOps
                pil_img = ImageOps.exif_transpose(pil_img)
            except Exception:
                pass

            orig_w, orig_h = pil_img.size
            format_name = pil_img.format or ("JPEG" if detected_mime == "image/jpeg" else "PNG")

            # In-place downscale if image exceeds 800px on any dimension
            if orig_w > 800 or orig_h > 800:
                pil_img.thumbnail((800, 800), Image.Resampling.BILINEAR)

            # Ensure RGB color mode for JPEG persistence
            save_fmt = "JPEG" if detected_mime == "image/jpeg" or format_name.upper() in ("JPEG", "JPG") else ("PNG" if detected_mime == "image/png" else "WEBP")
            if save_fmt == "JPEG" and pil_img.mode in ("RGBA", "P"):
                pil_img = pil_img.convert("RGB")

            width, height = pil_img.size

            # Save directly to disk (streaming directly to filesystem, no duplicate RAM buffer)
            pil_img.save(str(storage_path), format=save_fmt, quality=85, optimize=True)

        bio.close()
        del bio
    except ImageProcessingError:
        raise
    except Exception as e:
        raise ImageProcessingError(
            f"Corrupted or invalid image data: {str(e)}",
            details={"original_filename": original_filename},
        )
    finally:
        trim_process_memory()

    # Read actual saved size on disk
    saved_size = storage_path.stat().st_size
    logger.info(f"Persisted image {image_id} ({width}x{height}, {saved_size} bytes) at {storage_path}")

    return {
        "id": image_id,
        "filename": original_filename,
        "secure_filename": secure_filename,
        "storage_path": str(storage_path),
        "url": f"/uploads/{secure_filename}",
        "width": width,
        "height": height,
        "file_size_bytes": saved_size,
        "mime_type": detected_mime,
        "format": format_name,
    }
