from fastapi import APIRouter, UploadFile, File, Form, Depends, status
from fastapi.responses import FileResponse
from uuid import UUID, uuid4
from datetime import datetime
from pathlib import Path
from app.services.image_processing import validate_and_save_image
from app.schemas.image import ImageResponse
from app.core.exceptions import EntityNotFoundError
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/upload", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_image_endpoint(
    file: UploadFile = File(...),
    session_id: UUID = Form(default_factory=uuid4),
):
    """
    Secure Image Ingestion Endpoint:
    - Validates magic bytes (JPEG, PNG, WebP)
    - Validates file size limit (15MB)
    - Saves locally with secure UUID filename
    - Returns image metadata and URL
    """
    contents = await file.read()
    image_meta = await validate_and_save_image(
        file_bytes=contents,
        original_filename=file.filename or "uploaded_image.jpg",
    )

    return ImageResponse(
        id=image_meta["id"],
        session_id=session_id,
        filename=image_meta["filename"],
        file_size_bytes=image_meta["file_size_bytes"],
        width=image_meta["width"],
        height=image_meta["height"],
        mime_type=image_meta["mime_type"],
        url=image_meta["url"],
        detected_objects=[],
        created_at=datetime.utcnow(),
    )


@router.get("/{filename}/file")
async def get_image_file(filename: str):
    """
    Streams raw image bytes from local secure storage.
    """
    file_path = settings.UPLOAD_DIR / filename
    if not file_path.exists():
        raise EntityNotFoundError(f"Image {filename} not found.")

    return FileResponse(path=str(file_path))
