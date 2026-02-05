"""
Pydantic Schemas for API Request/Response Validation

Provides comprehensive data validation using Pydantic v2 models
for all API endpoints.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MessageRole(str, Enum):
    """Chat message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class HealthStatus(str, Enum):
    """Health check status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


# ============================================================
# Base Schemas
# ============================================================

class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


# ============================================================
# Authentication Schemas
# ============================================================

class UserRegisterRequest(BaseSchema):
    """User registration request schema."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username for registration",
        examples=["johndoe"],
    )
    email: str = Field(
        ...,
        min_length=5,
        max_length=255,
        description="User email address",
        examples=["john@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (min 8 characters)",
    )
    full_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="User's full name",
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLoginRequest(BaseSchema):
    """User login request schema."""

    username: str = Field(
        ...,
        description="Username or email",
        examples=["johndoe"],
    )
    password: str = Field(
        ...,
        description="User password",
    )


class TokenResponse(BaseSchema):
    """JWT token response schema."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


class TokenRefreshRequest(BaseSchema):
    """Token refresh request schema."""

    refresh_token: str = Field(..., description="JWT refresh token")


class UserResponse(BaseSchema):
    """User information response schema."""

    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    full_name: Optional[str] = Field(default=None, description="Full name")
    is_active: bool = Field(default=True, description="Account active status")
    roles: List[str] = Field(default_factory=list, description="User roles")
    created_at: datetime = Field(..., description="Account creation timestamp")


# ============================================================
# Chat Schemas
# ============================================================

class ChatMessage(BaseSchema):
    """Individual chat message schema."""

    role: MessageRole = Field(..., description="Message sender role")
    content: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Message content",
    )
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Message timestamp",
    )


class ChatRequest(BaseSchema):
    """Chat query request schema."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's chat query",
        examples=["What are the symptoms of diabetes?"],
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session ID for conversation context",
    )
    include_sources: bool = Field(
        default=False,
        description="Include source documents in response",
    )
    max_tokens: Optional[int] = Field(
        default=None,
        ge=1,
        le=2048,
        description="Maximum tokens for response",
    )

    @field_validator("query")
    @classmethod
    def sanitize_query(cls, v: str) -> str:
        """Sanitize and normalize query."""
        return v.strip()


class SourceDocument(BaseSchema):
    """Source document reference schema."""

    content: str = Field(..., description="Document content excerpt")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Document metadata",
    )
    score: Optional[float] = Field(
        default=None,
        description="Relevance score",
    )


class ChatResponse(BaseSchema):
    """Chat query response schema."""

    response: str = Field(..., description="Assistant's response")
    query: str = Field(..., description="Original query")
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for conversation tracking",
    )
    sources: List[SourceDocument] = Field(
        default_factory=list,
        description="Source documents used for response",
    )
    latency_ms: float = Field(..., description="Response latency in milliseconds")
    request_id: str = Field(..., description="Unique request identifier")


class ConversationHistory(BaseSchema):
    """Conversation history schema."""

    session_id: str = Field(..., description="Session identifier")
    messages: List[ChatMessage] = Field(
        default_factory=list,
        description="Conversation messages",
    )
    created_at: datetime = Field(..., description="Conversation start time")
    updated_at: datetime = Field(..., description="Last message time")


# ============================================================
# Health Check Schemas
# ============================================================

class ComponentHealth(BaseSchema):
    """Individual component health status."""

    name: str = Field(..., description="Component name")
    status: HealthStatus = Field(..., description="Component health status")
    latency_ms: Optional[float] = Field(
        default=None,
        description="Component latency in milliseconds",
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional health details",
    )
    last_check: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last health check timestamp",
    )


class HealthCheckResponse(BaseSchema):
    """Health check response schema."""

    status: HealthStatus = Field(..., description="Overall health status")
    version: str = Field(..., description="Application version")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")
    components: List[ComponentHealth] = Field(
        default_factory=list,
        description="Individual component health statuses",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Health check timestamp",
    )


class ReadinessResponse(BaseSchema):
    """Readiness check response schema."""

    ready: bool = Field(..., description="Application readiness status")
    checks: Dict[str, bool] = Field(
        default_factory=dict,
        description="Individual readiness checks",
    )


# ============================================================
# API Status Schemas
# ============================================================

class APIStatusResponse(BaseSchema):
    """API status response schema."""

    name: str = Field(..., description="API name")
    version: str = Field(..., description="API version")
    status: str = Field(..., description="API status")
    environment: str = Field(..., description="Deployment environment")
    documentation_url: str = Field(..., description="API documentation URL")


# ============================================================
# Error Schemas
# ============================================================

class ErrorDetail(BaseSchema):
    """Error detail schema."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional error details",
    )


class ErrorResponse(BaseSchema):
    """Standardized error response schema."""

    error: ErrorDetail = Field(..., description="Error information")
    request_id: Optional[str] = Field(
        default=None,
        description="Request identifier for debugging",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp",
    )


class ValidationErrorItem(BaseSchema):
    """Validation error item schema."""

    field: str = Field(..., description="Field with validation error")
    message: str = Field(..., description="Validation error message")
    type: str = Field(..., description="Error type")


class ValidationErrorResponse(BaseSchema):
    """Validation error response schema."""

    error: ErrorDetail = Field(..., description="Error information")
    validation_errors: List[ValidationErrorItem] = Field(
        ...,
        description="List of validation errors",
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Request identifier",
    )


# ============================================================
# Pagination Schemas
# ============================================================

class PaginationParams(BaseSchema):
    """Pagination parameters schema."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Items per page",
    )


class PaginatedResponse(BaseSchema):
    """Paginated response wrapper schema."""

    items: List[Any] = Field(..., description="Page items")
    total: int = Field(..., description="Total items count")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total pages count")
    has_next: bool = Field(..., description="Has next page")
    has_previous: bool = Field(..., description="Has previous page")


# ============================================================
# Audit Schemas
# ============================================================

class AuditLogEntry(BaseSchema):
    """Audit log entry schema."""

    id: str = Field(..., description="Audit log entry ID")
    event_type: str = Field(..., description="Type of event")
    action: str = Field(..., description="Action performed")
    user_id: Optional[str] = Field(default=None, description="User who performed action")
    resource_type: Optional[str] = Field(default=None, description="Type of resource")
    resource_id: Optional[str] = Field(default=None, description="Resource identifier")
    details: Dict[str, Any] = Field(default_factory=dict, description="Event details")
    ip_address: Optional[str] = Field(default=None, description="Client IP address")
    user_agent: Optional[str] = Field(default=None, description="Client user agent")
    timestamp: datetime = Field(..., description="Event timestamp")
    success: bool = Field(..., description="Action success status")
