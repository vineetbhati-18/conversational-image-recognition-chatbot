from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List, Optional
from app.models.image import ImageModel, DetectedObjectModel


class ImageRepository:
    """Repository handling all database persistence for images and detected objects."""

    @staticmethod
    async def create(
        db: AsyncSession,
        image_id: UUID,
        session_id: UUID,
        filename: str,
        storage_path: str,
        mime_type: str,
        file_size_bytes: int,
        width: int,
        height: int,
    ) -> ImageModel:
        db_image = ImageModel(
            id=image_id,
            session_id=session_id,
            filename=filename,
            storage_path=storage_path,
            mime_type=mime_type,
            file_size_bytes=file_size_bytes,
            width=width,
            height=height,
        )
        db.add(db_image)
        await db.commit()
        await db.refresh(db_image)
        return db_image

    @staticmethod
    async def get_by_id(db: AsyncSession, image_id: UUID, load_objects: bool = True) -> Optional[ImageModel]:
        query = select(ImageModel).where(ImageModel.id == image_id)
        if load_objects:
            query = query.options(selectinload(ImageModel.detected_objects))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def save_detected_objects(
        db: AsyncSession,
        image_id: UUID,
        detections: List[dict],
    ) -> List[DetectedObjectModel]:
        db_objs = []
        for d in detections:
            bbox = d.get("bbox", {})
            obj = DetectedObjectModel(
                image_id=image_id,
                class_name=d.get("class_name", "object"),
                confidence_score=d.get("confidence", 1.0),
                bbox_x_min=bbox.get("x_min", 0.0),
                bbox_y_min=bbox.get("y_min", 0.0),
                bbox_x_max=bbox.get("x_max", 0.0),
                bbox_y_max=bbox.get("y_max", 0.0),
            )
            db.add(obj)
            db_objs.append(obj)
        await db.commit()
        return db_objs
