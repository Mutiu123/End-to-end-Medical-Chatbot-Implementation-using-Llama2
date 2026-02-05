"""
Tests for Exception Module

Tests custom exception classes and error handling.
"""

import pytest

from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BadRequestError,
    BaseAPIException,
    ConflictError,
    DatabaseError,
    LLMError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)


class TestBaseAPIException:
    """Test cases for BaseAPIException."""

    def test_default_values(self):
        """Test exception with default values."""
        exc = BaseAPIException(message="Test error")

        assert exc.message == "Test error"
        assert exc.status_code == 500
        assert exc.error_code == "INTERNAL_ERROR"
        assert exc.details == {}

    def test_custom_values(self):
        """Test exception with custom values."""
        exc = BaseAPIException(
            message="Custom error",
            status_code=400,
            error_code="CUSTOM_ERROR",
            details={"field": "value"},
        )

        assert exc.message == "Custom error"
        assert exc.status_code == 400
        assert exc.error_code == "CUSTOM_ERROR"
        assert exc.details["field"] == "value"

    def test_to_dict(self):
        """Test exception serialization to dictionary."""
        exc = BaseAPIException(
            message="Test error",
            error_code="TEST_ERROR",
            details={"key": "value"},
        )

        result = exc.to_dict()

        assert result["error"]["code"] == "TEST_ERROR"
        assert result["error"]["message"] == "Test error"
        assert result["error"]["details"]["key"] == "value"


class TestAuthenticationError:
    """Test cases for AuthenticationError."""

    def test_default_message(self):
        """Test default authentication error."""
        exc = AuthenticationError()

        assert exc.message == "Authentication failed"
        assert exc.status_code == 401
        assert exc.error_code == "AUTHENTICATION_ERROR"

    def test_custom_message(self):
        """Test custom authentication error message."""
        exc = AuthenticationError(message="Invalid token")

        assert exc.message == "Invalid token"
        assert exc.status_code == 401


class TestAuthorizationError:
    """Test cases for AuthorizationError."""

    def test_default_message(self):
        """Test default authorization error."""
        exc = AuthorizationError()

        assert exc.message == "Insufficient permissions"
        assert exc.status_code == 403
        assert exc.error_code == "AUTHORIZATION_ERROR"


class TestValidationError:
    """Test cases for ValidationError."""

    def test_validation_error(self):
        """Test validation error."""
        exc = ValidationError(
            message="Invalid input",
            details={"field": "email", "error": "Invalid format"},
        )

        assert exc.status_code == 422
        assert exc.error_code == "VALIDATION_ERROR"


class TestNotFoundError:
    """Test cases for NotFoundError."""

    def test_not_found_error(self):
        """Test not found error."""
        exc = NotFoundError(
            message="User not found",
            resource_type="User",
            resource_id="123",
        )

        assert exc.status_code == 404
        assert exc.error_code == "NOT_FOUND"
        assert exc.details["resource_type"] == "User"
        assert exc.details["resource_id"] == "123"


class TestRateLimitError:
    """Test cases for RateLimitError."""

    def test_rate_limit_error(self):
        """Test rate limit error."""
        exc = RateLimitError(
            retry_after=60,
            limit=100,
        )

        assert exc.status_code == 429
        assert exc.error_code == "RATE_LIMIT_EXCEEDED"
        assert exc.details["retry_after"] == 60
        assert exc.details["limit"] == 100


class TestDatabaseError:
    """Test cases for DatabaseError."""

    def test_database_error(self):
        """Test database error."""
        exc = DatabaseError(
            message="Connection failed",
            operation="insert",
        )

        assert exc.status_code == 503
        assert exc.error_code == "DATABASE_ERROR"
        assert exc.details["operation"] == "insert"


class TestLLMError:
    """Test cases for LLMError."""

    def test_llm_error(self):
        """Test LLM error."""
        exc = LLMError(
            message="Model inference failed",
            details={"model": "llama-2"},
        )

        assert exc.status_code == 503
        assert exc.error_code == "LLM_ERROR"


class TestConflictError:
    """Test cases for ConflictError."""

    def test_conflict_error(self):
        """Test conflict error."""
        exc = ConflictError(message="Username already exists")

        assert exc.status_code == 409
        assert exc.error_code == "CONFLICT"


class TestBadRequestError:
    """Test cases for BadRequestError."""

    def test_bad_request_error(self):
        """Test bad request error."""
        exc = BadRequestError(message="Invalid request format")

        assert exc.status_code == 400
        assert exc.error_code == "BAD_REQUEST"
