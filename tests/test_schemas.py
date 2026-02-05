"""
Tests for Pydantic Schemas

Tests request/response validation models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError


class TestUserSchemas:
    """Test cases for user-related schemas."""

    def test_user_register_valid(self):
        """Test valid user registration schema."""
        from app.api.schemas import UserRegisterRequest

        data = UserRegisterRequest(
            username="testuser",
            email="test@example.com",
            password="TestPass123!",
            full_name="Test User",
        )

        assert data.username == "testuser"
        assert data.email == "test@example.com"

    def test_user_register_invalid_email(self):
        """Test user registration with invalid email."""
        from app.api.schemas import UserRegisterRequest

        with pytest.raises(ValidationError) as exc_info:
            UserRegisterRequest(
                username="testuser",
                email="invalid-email",
                password="TestPass123!",
            )

        assert "email" in str(exc_info.value).lower()

    def test_user_register_weak_password(self):
        """Test user registration with weak password."""
        from app.api.schemas import UserRegisterRequest

        with pytest.raises(ValidationError) as exc_info:
            UserRegisterRequest(
                username="testuser",
                email="test@example.com",
                password="weakpass",
            )

        assert "password" in str(exc_info.value).lower()

    def test_user_register_short_username(self):
        """Test user registration with short username."""
        from app.api.schemas import UserRegisterRequest

        with pytest.raises(ValidationError):
            UserRegisterRequest(
                username="ab",
                email="test@example.com",
                password="TestPass123!",
            )

    def test_user_login_valid(self):
        """Test valid user login schema."""
        from app.api.schemas import UserLoginRequest

        data = UserLoginRequest(
            username="testuser",
            password="TestPass123!",
        )

        assert data.username == "testuser"


class TestChatSchemas:
    """Test cases for chat-related schemas."""

    def test_chat_request_valid(self):
        """Test valid chat request schema."""
        from app.api.schemas import ChatRequest

        data = ChatRequest(
            query="What are the symptoms of diabetes?",
            session_id="test-session",
            include_sources=True,
        )

        assert data.query == "What are the symptoms of diabetes?"
        assert data.session_id == "test-session"
        assert data.include_sources is True

    def test_chat_request_strips_whitespace(self):
        """Test chat request strips whitespace from query."""
        from app.api.schemas import ChatRequest

        data = ChatRequest(
            query="  What is diabetes?  ",
        )

        assert data.query == "What is diabetes?"

    def test_chat_request_empty_query(self):
        """Test chat request with empty query."""
        from app.api.schemas import ChatRequest

        with pytest.raises(ValidationError):
            ChatRequest(query="")

    def test_chat_request_max_tokens_validation(self):
        """Test chat request max_tokens validation."""
        from app.api.schemas import ChatRequest

        with pytest.raises(ValidationError):
            ChatRequest(
                query="Test query",
                max_tokens=5000,  # Exceeds maximum
            )

    def test_chat_response_schema(self):
        """Test chat response schema."""
        from app.api.schemas import ChatResponse

        data = ChatResponse(
            response="Diabetes symptoms include...",
            query="What are the symptoms?",
            session_id="test-session",
            sources=[],
            latency_ms=150.5,
            request_id="req-123",
        )

        assert data.response == "Diabetes symptoms include..."
        assert data.latency_ms == 150.5

    def test_source_document_schema(self):
        """Test source document schema."""
        from app.api.schemas import SourceDocument

        data = SourceDocument(
            content="Medical text content...",
            metadata={"page": 1, "source": "medical_book.pdf"},
            score=0.95,
        )

        assert data.content == "Medical text content..."
        assert data.score == 0.95


class TestHealthSchemas:
    """Test cases for health check schemas."""

    def test_health_check_response(self):
        """Test health check response schema."""
        from app.api.schemas import HealthCheckResponse, HealthStatus

        data = HealthCheckResponse(
            status=HealthStatus.HEALTHY,
            version="1.0.0",
            uptime_seconds=3600.5,
            components=[],
        )

        assert data.status == HealthStatus.HEALTHY
        assert data.version == "1.0.0"

    def test_component_health_schema(self):
        """Test component health schema."""
        from app.api.schemas import ComponentHealth, HealthStatus

        data = ComponentHealth(
            name="database",
            status=HealthStatus.HEALTHY,
            latency_ms=5.2,
            details={"connected": True},
        )

        assert data.name == "database"
        assert data.latency_ms == 5.2

    def test_readiness_response(self):
        """Test readiness response schema."""
        from app.api.schemas import ReadinessResponse

        data = ReadinessResponse(
            ready=True,
            checks={"database": True, "api": True},
        )

        assert data.ready is True
        assert data.checks["database"] is True


class TestErrorSchemas:
    """Test cases for error response schemas."""

    def test_error_response_schema(self):
        """Test error response schema."""
        from app.api.schemas import ErrorDetail, ErrorResponse

        error_detail = ErrorDetail(
            code="VALIDATION_ERROR",
            message="Invalid input",
            details={"field": "email"},
        )

        data = ErrorResponse(error=error_detail)

        assert data.error.code == "VALIDATION_ERROR"
        assert data.error.message == "Invalid input"

    def test_validation_error_response(self):
        """Test validation error response schema."""
        from app.api.schemas import (
            ErrorDetail,
            ValidationErrorItem,
            ValidationErrorResponse,
        )

        error_detail = ErrorDetail(
            code="VALIDATION_ERROR",
            message="Validation failed",
            details={},
        )

        validation_errors = [
            ValidationErrorItem(
                field="email",
                message="Invalid email format",
                type="value_error",
            )
        ]

        data = ValidationErrorResponse(
            error=error_detail,
            validation_errors=validation_errors,
        )

        assert len(data.validation_errors) == 1
        assert data.validation_errors[0].field == "email"


class TestPaginationSchemas:
    """Test cases for pagination schemas."""

    def test_pagination_params(self):
        """Test pagination parameters schema."""
        from app.api.schemas import PaginationParams

        data = PaginationParams(page=2, page_size=50)

        assert data.page == 2
        assert data.page_size == 50

    def test_pagination_params_defaults(self):
        """Test pagination parameters defaults."""
        from app.api.schemas import PaginationParams

        data = PaginationParams()

        assert data.page == 1
        assert data.page_size == 20

    def test_paginated_response(self):
        """Test paginated response schema."""
        from app.api.schemas import PaginatedResponse

        data = PaginatedResponse(
            items=["item1", "item2"],
            total=100,
            page=1,
            page_size=20,
            total_pages=5,
            has_next=True,
            has_previous=False,
        )

        assert len(data.items) == 2
        assert data.total == 100
        assert data.has_next is True
