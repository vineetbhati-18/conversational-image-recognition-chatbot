from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import List, Optional, Dict, Any
from app.models.message import MessageModel


class MessageRepository:
    """Repository handling all database persistence for dialogue history."""

    @staticmethod
    async def create(
        db: AsyncSession,
        session_id: UUID,
        sender_type: str,
        content: str,
        image_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MessageModel:
        msg = MessageModel(
            session_id=session_id,
            image_id=image_id,
            sender_type=sender_type,
            content=content,
            metadata_payload=metadata or {},
        )
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        return msg

    @staticmethod
    async def get_by_session(
        db: AsyncSession,
        session_id: UUID,
        limit: int = 50,
    ) -> List[MessageModel]:
        query = (
            select(MessageModel)
            .where(MessageModel.session_id == session_id)
            .order_by(MessageModel.created_at.asc())
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())
