"""
API v1 Router registry.
"""
from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.images import router as images_router
from app.api.v1.sessions import router as sessions_router
from app.api.v1.chat import router as chat_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["Health"])
api_router.include_router(images_router, prefix="/images", tags=["Images"])
api_router.include_router(sessions_router, prefix="/sessions", tags=["Sessions"])
api_router.include_router(chat_router, prefix="/chat", tags=["Chat"])
