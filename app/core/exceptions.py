"""
Custom Exception Definitions

Provides structured exception handling with proper HTTP status codes
and consistent error response format across the application.
"""

from typing import Any, Dict, Optional


class BaseAPIException(Exception):
    """
    Base exception for all API errors.

    Provides consistent error structure with status code,
    error code, and detailed message.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
            }
        }


class AuthenticationError(BaseAPIException):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
            details=details,
        )


class AuthorizationError(BaseAPIException):
    """Raised when user lacks required permissions."""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
            details=details,
        )


class ValidationError(BaseAPIException):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class NotFoundError(BaseAPIException):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: str = "Resource",
        resource_id: Optional[str] = None,
    ):
        details = {"resource_type": resource_type}
        if resource_id:
            details["resource_id"] = resource_id
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            details=details,
        )


class RateLimitError(BaseAPIException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        limit: Optional[int] = None,
    ):
        details = {}
        if retry_after is not None:
            details["retry_after"] = retry_after
        if limit is not None:
            details["limit"] = limit
        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details,
        )


class DatabaseError(BaseAPIException):
    """Raised when database operations fail."""

    def __init__(
        self,
        message: str = "Database operation failed",
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if operation:
            error_details["operation"] = operation
        super().__init__(
            message=message,
            status_code=503,
            error_code="DATABASE_ERROR",
            details=error_details,
        )


class ExternalServiceError(BaseAPIException):
    """Raised when external service calls fail."""

    def __init__(
        self,
        message: str = "External service unavailable",
        service_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if service_name:
            error_details["service"] = service_name
        super().__init__(
            message=message,
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=error_details,
        )


class LLMError(BaseAPIException):
    """Raised when LLM processing fails."""

    def __init__(
        self,
        message: str = "LLM processing failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=503,
            error_code="LLM_ERROR",
            details=details,
        )


class VectorStoreError(BaseAPIException):
    """Raised when vector store operations fail."""

    def __init__(
        self,
        message: str = "Vector store operation failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=503,
            error_code="VECTOR_STORE_ERROR",
            details=details,
        )


class ConfigurationError(BaseAPIException):
    """Raised when configuration is invalid."""

    def __init__(
        self,
        message: str = "Configuration error",
        config_key: Optional[str] = None,
    ):
        details = {}
        if config_key:
            details["config_key"] = config_key
        super().__init__(
            message=message,
            status_code=500,
            error_code="CONFIGURATION_ERROR",
            details=details,
        )


class ConflictError(BaseAPIException):
    """Raised when there is a resource conflict."""

    def __init__(
        self,
        message: str = "Resource conflict",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
            details=details,
        )


class BadRequestError(BaseAPIException):
    """Raised when request is malformed."""

    def __init__(
        self,
        message: str = "Bad request",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            status_code=400,
            error_code="BAD_REQUEST",
            details=details,
        )


class ServiceUnavailableError(BaseAPIException):
    """Raised when service is temporarily unavailable."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        retry_after: Optional[int] = None,
    ):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(
            message=message,
            status_code=503,
            error_code="SERVICE_UNAVAILABLE",
            details=details,
        )


class SecurityViolationError(BaseAPIException):
    """Raised when a security violation is detected."""

    def __init__(
        self,
        message: str = "Security violation detected",
        violation_type: Optional[str] = None,
    ):
        details = {}
        if violation_type:
            details["violation_type"] = violation_type
        super().__init__(
            message=message,
            status_code=400,
            error_code="SECURITY_VIOLATION",
            details=details,
        )
