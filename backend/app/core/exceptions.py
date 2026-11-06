from fastapi import Request, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("bel_chatbot.exceptions")


class AppException(Exception):
    """Base application exception."""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class ImageProcessingError(AppException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=422, details=details)


class ModelInferenceError(AppException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, details=details)


class EntityNotFoundError(AppException):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND, details=details)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.error(f"Application error: {exc.message} on {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.message,
            "details": exc.details,
            "path": str(request.url.path),
        },
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled server error on {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "An internal server error occurred.",
            "path": str(request.url.path),
        },
    )
