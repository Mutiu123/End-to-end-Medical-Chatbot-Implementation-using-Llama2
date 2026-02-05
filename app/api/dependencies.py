"""
API Dependencies

Provides dependency injection for FastAPI routes including:
- Authentication dependencies
- Rate limiting
- Database connections
- Request context
"""

import time
import uuid
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
)
from app.core.logging import get_logger, request_id_var
from app.core.metrics import metrics
from app.core.security import (
    InputSanitizer,
    SecurityUtils,
    TokenData,
    rate_limiter,
)
from app.db.mongodb import get_database


logger = get_logger(__name__)


# Security scheme for JWT authentication
security_scheme = HTTPBearer(auto_error=False)


async def get_request_id(
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-ID")
) -> str:
    """
    Get or generate a unique request ID.

    Args:
        x_request_id: Optional request ID from header

    Returns:
        Request ID string
    """
    request_id = x_request_id or str(uuid.uuid4())
    request_id_var.set(request_id)
    return request_id


async def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.

    Handles X-Forwarded-For header for proxied requests.

    Args:
        request: FastAPI request object

    Returns:
        Client IP address string
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Get the first IP in the chain (original client)
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def rate_limit_dependency(
    request: Request,
    client_ip: str = Depends(get_client_ip),
) -> None:
    """
    Rate limiting dependency using token bucket algorithm.

    Args:
        request: FastAPI request object
        client_ip: Client IP address

    Raises:
        RateLimitError: If rate limit is exceeded
    """
    # Create rate limit key based on IP and endpoint
    endpoint = request.url.path
    rate_limit_key = f"{client_ip}:{endpoint}"

    allowed, info = rate_limiter.is_allowed(rate_limit_key)

    # Set rate limit headers
    request.state.rate_limit_info = info

    if not allowed:
        wait_time = rate_limiter.get_wait_time(rate_limit_key)
        metrics.rate_limit_hits_total.labels(endpoint=endpoint).inc()
        logger.warning(
            f"Rate limit exceeded for {client_ip} on {endpoint}",
            extra={"extra_data": {"client_ip": client_ip, "endpoint": endpoint}}
        )
        raise RateLimitError(
            message="Rate limit exceeded. Please try again later.",
            retry_after=int(wait_time) + 1,
            limit=info["limit"],
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Optional[TokenData]:
    """
    Get current authenticated user from JWT token.

    This dependency does not require authentication - returns None if no token.

    Args:
        credentials: Optional HTTP Bearer credentials

    Returns:
        TokenData if authenticated, None otherwise
    """
    if credentials is None:
        return None

    token_data = SecurityUtils.verify_token(credentials.credentials)
    if token_data is None:
        return None

    if SecurityUtils.is_token_expired(token_data):
        return None

    return token_data


async def require_authentication(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> TokenData:
    """
    Require authenticated user.

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        TokenData for authenticated user

    Raises:
        AuthenticationError: If authentication fails
    """
    if credentials is None:
        metrics.auth_attempts_total.labels(method="bearer", status="missing").inc()
        raise AuthenticationError(
            message="Authentication required",
            details={"reason": "No credentials provided"},
        )

    token_data = SecurityUtils.verify_token(credentials.credentials)

    if token_data is None:
        metrics.auth_attempts_total.labels(method="bearer", status="invalid").inc()
        raise AuthenticationError(
            message="Invalid authentication token",
            details={"reason": "Token verification failed"},
        )

    if SecurityUtils.is_token_expired(token_data):
        metrics.auth_attempts_total.labels(method="bearer", status="expired").inc()
        raise AuthenticationError(
            message="Token has expired",
            details={"reason": "Token expired"},
        )

    metrics.auth_attempts_total.labels(method="bearer", status="success").inc()
    return token_data


def require_roles(*required_roles: str):
    """
    Create a dependency that requires specific user roles.

    Args:
        required_roles: Roles required for access

    Returns:
        Dependency function that validates roles
    """
    async def role_checker(
        token_data: TokenData = Depends(require_authentication),
    ) -> TokenData:
        """Check if user has required roles."""
        user_roles = set(token_data.roles)
        required = set(required_roles)

        if not required.intersection(user_roles):
            raise AuthorizationError(
                message="Insufficient permissions",
                details={
                    "required_roles": list(required_roles),
                    "user_roles": list(token_data.roles),
                },
            )

        return token_data

    return role_checker


async def get_db():
    """
    Get database connection dependency.

    Yields:
        MongoDB database instance
    """
    db = await get_database()
    yield db


class RequestTimer:
    """Context manager for request timing."""

    def __init__(self):
        self.start_time: float = 0
        self.end_time: float = 0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()

    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        return (self.end_time - self.start_time) * 1000

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds."""
        return self.end_time - self.start_time


async def validate_content_type(
    request: Request,
    expected_type: str = "application/json",
) -> None:
    """
    Validate request content type.

    Args:
        request: FastAPI request object
        expected_type: Expected content type

    Raises:
        HTTPException: If content type is invalid
    """
    content_type = request.headers.get("Content-Type", "")
    if expected_type not in content_type:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Content-Type must be {expected_type}",
        )


async def sanitize_request_body(request: Request) -> dict:
    """
    Parse and sanitize request body.

    Args:
        request: FastAPI request object

    Returns:
        Sanitized request body dictionary
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body",
        )

    # Sanitize string values in body
    sanitized = {}
    for key, value in body.items():
        if isinstance(value, str):
            sanitized[key] = InputSanitizer.sanitize_query(value)
        else:
            sanitized[key] = value

    return sanitized
