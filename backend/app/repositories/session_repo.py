from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List, Optional
from app.models.session import SessionModel


class SessionRepository:
    """Repository handling all database persistence for conversation sessions."""

    @staticmethod
    async def create(db: AsyncSession, title: str = "New Conversation", session_id: Optional[UUID] = None) -> SessionModel:
        session = SessionModel(id=session_id, title=title) if session_id else SessionModel(title=title)
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def get_by_id(db: AsyncSession, session_id: UUID, load_relations: bool = True) -> Optional[SessionModel]:
        query = select(SessionModel).where(SessionModel.id == session_id)
        if load_relations:
            query = query.options(
                selectinload(SessionModel.messages),
                selectinload(SessionModel.images),
            )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_recent(db: AsyncSession, limit: int = 50, offset: int = 0) -> List[SessionModel]:
        query = select(SessionModel).order_by(desc(SessionModel.updated_at)).limit(limit).offset(offset)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def delete(db: AsyncSession, session: SessionModel) -> None:
        await db.delete(session)
        await db.commit()
