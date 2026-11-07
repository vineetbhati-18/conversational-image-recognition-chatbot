from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging

from app.config import get_settings
from app.core.exceptions import AppException, app_exception_handler, global_exception_handler
from app.core.logging_middleware import RequestLoggingMiddleware
from app.utils.logger import setup_logger, get_logger
from app.core.database import engine, init_db
import app.models  # Register all models for create_all
from app.api.v1 import api_router

# Initialize structured logging
setup_logger("bel_chatbot")
logger = get_logger("main")
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

    # 2. Verify Database Connection and initialize schema
    try:
        await init_db()
        logger.info("Successfully initialized database tables in PostgreSQL.")
    except Exception as e:
        logger.warning(f"Database schema initialization warning: {e}")

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
    cors_origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Audit & Latency Logging Middleware
    app.add_middleware(RequestLoggingMiddleware)

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
            "message": "Welcome to BEL Conversational Image Recognition API",
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
