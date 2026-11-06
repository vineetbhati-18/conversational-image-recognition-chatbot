from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.core.database import get_db
from app.repositories.session_repo import SessionRepository
from app.schemas.session import SessionCreate, SessionResponse, SessionDetailResponse
from app.core.exceptions import EntityNotFoundError

router = APIRouter()


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate = None,
    db: AsyncSession = Depends(get_db),
):
    title = payload.title if payload and payload.title else "New Conversation"
    return await SessionRepository.create(db, title=title)


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    return await SessionRepository.list_recent(db, limit=limit, offset=offset)


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    session = await SessionRepository.get_by_id(db, session_id, load_relations=True)
    if not session:
        raise EntityNotFoundError(f"Session {session_id} not found.")
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    session = await SessionRepository.get_by_id(db, session_id, load_relations=False)
    if not session:
        raise EntityNotFoundError(f"Session {session_id} not found.")
    await SessionRepository.delete(db, session)
    return None
