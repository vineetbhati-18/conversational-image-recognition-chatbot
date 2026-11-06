import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.utils.logger import get_logger

logger = get_logger("http_access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for audit logging and performance metrics:
    - Generates and injects 'X-Request-ID' header
    - Records request duration in milliseconds
    - Logs response code and client telemetry
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]

        # Attach request_id to request state
        request.state.request_id = request_id

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Inject request ID and latency headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

            logger.info(
                f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.2f}ms)",
                extra={"request_id": request_id},
            )
            return response
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"{request.method} {request.url.path} failed after {duration_ms:.2f}ms: {exc}",
                extra={"request_id": request_id},
            )
            raise exc
