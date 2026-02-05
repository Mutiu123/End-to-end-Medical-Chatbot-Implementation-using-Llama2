"""
Request Handler Middleware

Provides middleware components for:
- Request context management
- Security headers
- Global exception handling
- Request/response logging
"""

import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.exceptions import BaseAPIException
from app.core.logging import get_logger, request_id_var
from app.core.metrics import metrics


logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request context management.

    Handles:
    - Request ID generation/propagation
    - Request timing
    - Request/response logging
    - Metrics collection
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with context management."""
        # Generate or get request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_var.set(request_id)

        # Start timing
        start_time = time.perf_counter()

        # Track active requests
        endpoint = request.url.path
        method = request.method
        metrics.active_requests.labels(method=method, endpoint=endpoint).inc()

        # Log request
        logger.info(
            f"Request started: {method} {endpoint}",
            extra={
                "extra_data": {
                    "method": method,
                    "path": endpoint,
                    "client_ip": self._get_client_ip(request),
                    "user_agent": request.headers.get("User-Agent", "unknown"),
                }
            }
        )

        try:
            response = await call_next(request)

            # Calculate latency
            latency = time.perf_counter() - start_time

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            # Add rate limit headers if available
            if hasattr(request.state, "rate_limit_info"):
                info = request.state.rate_limit_info
                response.headers["X-RateLimit-Limit"] = str(info.get("limit", 0))
                response.headers["X-RateLimit-Remaining"] = str(info.get("remaining", 0))
                response.headers["X-RateLimit-Reset"] = str(info.get("reset", 0))

            # Track metrics
            metrics.track_request(
                method=method,
                endpoint=endpoint,
                status_code=response.status_code,
                latency=latency,
            )

            # Log response
            logger.info(
                f"Request completed: {method} {endpoint} - {response.status_code}",
                extra={
                    "extra_data": {
                        "status_code": response.status_code,
                        "latency_ms": round(latency * 1000, 2),
                    }
                }
            )

            return response

        finally:
            metrics.active_requests.labels(method=method, endpoint=endpoint).dec()

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to responses.

    Implements security best practices including:
    - Content Security Policy
    - X-Frame-Options
    - X-Content-Type-Options
    - Strict-Transport-Security
    """

    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Cache-Control": "no-store, no-cache, must-revalidate",
        "Pragma": "no-cache",
    }

    # Add HSTS header only in production
    PRODUCTION_HEADERS = {
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)

        # Add base security headers
        for header, value in self.SECURITY_HEADERS.items():
            response.headers[header] = value

        # Add production-only headers
        if settings.is_production:
            for header, value in self.PRODUCTION_HEADERS.items():
                response.headers[header] = value

        # Add CSP header
        csp = self._build_csp()
        response.headers["Content-Security-Policy"] = csp

        return response

    def _build_csp(self) -> str:
        """Build Content Security Policy header."""
        directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline'",
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        return "; ".join(directives)


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """
    Global exception handler middleware.

    Catches all unhandled exceptions and returns
    consistent error responses.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle exceptions globally."""
        try:
            return await call_next(request)

        except BaseAPIException as e:
            # Handle custom API exceptions
            logger.warning(
                f"API exception: {e.error_code} - {e.message}",
                extra={"extra_data": {"details": e.details}}
            )

            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": {
                        "code": e.error_code,
                        "message": e.message,
                        "details": e.details,
                    },
                    "request_id": request_id_var.get(),
                },
            )

        except Exception as e:
            # Handle unexpected exceptions
            logger.error(
                f"Unhandled exception: {str(e)}",
                exc_info=True,
            )

            # Don't expose internal errors in production
            message = str(e) if settings.debug else "Internal server error"

            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": message,
                        "details": {},
                    },
                    "request_id": request_id_var.get(),
                },
            )


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Set up exception handlers for FastAPI application.

    Args:
        app: FastAPI application instance
    """
    from fastapi.exceptions import RequestValidationError
    from pydantic import ValidationError

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Handle request validation errors."""
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })

        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": {"errors": errors},
                },
                "request_id": request_id_var.get(),
            },
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(
        request: Request,
        exc: ValidationError,
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Data validation failed",
                    "details": {"errors": exc.errors()},
                },
                "request_id": request_id_var.get(),
            },
        )

    @app.exception_handler(BaseAPIException)
    async def api_exception_handler(
        request: Request,
        exc: BaseAPIException,
    ) -> JSONResponse:
        """Handle custom API exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                },
                "request_id": request_id_var.get(),
            },
        )
