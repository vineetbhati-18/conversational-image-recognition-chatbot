from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.models.session import SessionModel
from app.models.message import MessageModel
from app.schemas.session import SessionCreate, SessionResponse, SessionDetailResponse
from app.schemas.chat import MessageResponse
from app.core.exceptions import EntityNotFoundError

router = APIRouter()


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Creates a new conversation session.
    """
    title = payload.title if payload and payload.title else "New Conversation"
    session = SessionModel(title=title)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """
    Lists conversation sessions ordered by most recent update.
    """
    query = (
        select(SessionModel)
        .order_by(desc(SessionModel.updated_at))
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    sessions = result.scalars().all()
    return sessions


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves full details of a session, including message dialogue history.
    """
    query = (
        select(SessionModel)
        .where(SessionModel.id == session_id)
        .options(selectinload(SessionModel.messages), selectinload(SessionModel.images))
    )
    result = await db.execute(query)
    session = result.scalar_one_or_none()

    if not session:
        raise EntityNotFoundError(f"Session {session_id} not found.")

    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Deletes a conversation session and cascades all messages, images, and detections.
    """
    query = select(SessionModel).where(SessionModel.id == session_id)
    result = await db.execute(query)
    session = result.scalar_one_or_none()

    if not session:
        raise EntityNotFoundError(f"Session {session_id} not found.")

    await db.delete(session)
    await db.commit()
    return None
