from fastapi import APIRouter, UploadFile, File, Form, Depends, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID, uuid4
from datetime import datetime
from pathlib import Path

from app.core.database import get_db
from app.repositories.session_repo import SessionRepository
from app.repositories.image_repo import ImageRepository
from app.services.image_processing import validate_and_save_image
from app.services.yolo_service import get_yolo_service
from app.schemas.image import ImageResponse, DetectedObjectSchema, BoundingBox
from app.core.exceptions import EntityNotFoundError
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/upload", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_image_endpoint(
    file: UploadFile = File(...),
    session_id: UUID = Form(default_factory=uuid4),
    db: AsyncSession = Depends(get_db),
):
    # 1. Ensure target session exists in DB (or create automatically)
    session = await SessionRepository.get_by_id(db, session_id, load_relations=False)
    if not session:
        session = await SessionRepository.create(
            db, title=f"Recon ({file.filename or 'Image'})", session_id=session_id
        )

    # 2. Ingest and save image file
    contents = await file.read()
    image_meta = await validate_and_save_image(
        file_bytes=contents,
        original_filename=file.filename or "uploaded_image.jpg",
    )

    # 3. Save Image record via Repository
    db_image = await ImageRepository.create(
        db,
        image_id=image_meta["id"],
        session_id=session_id,
        filename=image_meta["filename"],
        storage_path=image_meta["storage_path"],
        mime_type=image_meta["mime_type"],
        file_size_bytes=image_meta["file_size_bytes"],
        width=image_meta["width"],
        height=image_meta["height"],
    )

    # 4. Run real YOLOv8 detection pass offloaded to worker thread to prevent blocking event loop
    import asyncio
    yolo = get_yolo_service()
    detection_results = await asyncio.to_thread(
        yolo.detect_objects,
        image_source=image_meta["storage_path"],
        conf_threshold=settings.CONFIDENCE_THRESHOLD,
    )

    # 5. Persist detected objects to PostgreSQL via Repository
    await ImageRepository.save_detected_objects(
        db,
        image_id=db_image.id,
        detections=detection_results["detections"],
    )

    detected_schemas = [
        DetectedObjectSchema(
            id=UUID(d["id"]),
            class_name=d["class_name"],
            confidence=d["confidence"],
            bbox=BoundingBox(
                x_min=d["bbox"]["x_min"],
                y_min=d["bbox"]["y_min"],
                x_max=d["bbox"]["x_max"],
                y_max=d["bbox"]["y_max"],
            ),
        )
        for d in detection_results["detections"]
    ]

    return ImageResponse(
        id=db_image.id,
        session_id=session_id,
        filename=db_image.filename,
        file_size_bytes=db_image.file_size_bytes,
        width=db_image.width,
        height=db_image.height,
        mime_type=db_image.mime_type,
        url=image_meta["url"],
        detected_objects=detected_schemas,
        created_at=db_image.created_at,
    )


@router.post("/{image_id}/detect", response_model=ImageResponse)
async def rerun_detection_endpoint(
    image_id: UUID,
    confidence_threshold: float = Query(default=0.35, ge=0.05, le=0.95),
    db: AsyncSession = Depends(get_db),
):
    image = await ImageRepository.get_by_id(db, image_id, load_objects=False)
    if not image:
        raise EntityNotFoundError(f"Image {image_id} not found.")

    yolo = get_yolo_service()
    detection_results = yolo.detect_objects(
        image_source=image.storage_path,
        conf_threshold=confidence_threshold,
    )

    detected_schemas = [
        DetectedObjectSchema(
            id=UUID(d["id"]),
            class_name=d["class_name"],
            confidence=d["confidence"],
            bbox=BoundingBox(
                x_min=d["bbox"]["x_min"],
                y_min=d["bbox"]["y_min"],
                x_max=d["bbox"]["x_max"],
                y_max=d["bbox"]["y_max"],
            ),
        )
        for d in detection_results["detections"]
    ]

    return ImageResponse(
        id=image.id,
        session_id=image.session_id,
        filename=image.filename,
        file_size_bytes=image.file_size_bytes,
        width=image.width,
        height=image.height,
        mime_type=image.mime_type,
        url=f"/uploads/{Path(image.storage_path).name}",
        detected_objects=detected_schemas,
        created_at=image.created_at,
    )


@router.get("/{filename}/file")
async def get_image_file(filename: str):
    file_path = settings.UPLOAD_DIR / filename
    if not file_path.exists():
        raise EntityNotFoundError(f"Image {filename} not found.")
    return FileResponse(path=str(file_path))
