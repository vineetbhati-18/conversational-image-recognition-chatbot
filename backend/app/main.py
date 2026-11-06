from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging

from app.config import get_settings
from app.core.exceptions import AppException, app_exception_handler, global_exception_handler
from app.core.database import engine
from app.api.v1 import api_router

logger = logging.getLogger("bel_chatbot")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager:
    - Creates necessary filesystem paths on startup.
    - Verifies async database engine connectivity.
    - Cleans up connection pools on shutdown.
    """
    # 1. Ensure storage directories exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info(f"Initialized image storage at: {settings.UPLOAD_DIR}")

    # 2. Verify Database Connection
    try:
        async with engine.connect() as conn:
            logger.info("Successfully connected to PostgreSQL engine.")
    except Exception as e:
        logger.warning(f"Database connection warning on startup: {e}")

    yield

    # 3. Graceful shutdown
    await engine.dispose()
    logger.info("Database connection pool disposed.")


def create_app() -> FastAPI:
    """
    FastAPI Application Factory.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Conversational Image Recognition Chatbot Backend for Bharat Electronics Limited (BEL)",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception Handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    # Static file serving for uploaded imagery
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")

    # API v1 routes
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/")
    async def root():
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "active",
            "docs": "/docs",
            "health": f"{settings.API_V1_PREFIX}/health",
        }

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
