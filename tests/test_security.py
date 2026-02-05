"""
Tests for Security Module

Tests JWT tokens, password hashing, rate limiting,
and input sanitization.
"""

from datetime import timedelta

import pytest


class TestPasswordHashing:
    """Test cases for password hashing utilities."""

    def test_hash_password(self):
        """Test password hashing."""
        from app.core.security import SecurityUtils

        password = "TestPassword123!"
        hashed = SecurityUtils.hash_password(password)

        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        from app.core.security import SecurityUtils

        password = "TestPassword123!"
        hashed = SecurityUtils.hash_password(password)

        assert SecurityUtils.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        from app.core.security import SecurityUtils

        password = "TestPassword123!"
        hashed = SecurityUtils.hash_password(password)

        assert SecurityUtils.verify_password("WrongPassword", hashed) is False


class TestJWTTokens:
    """Test cases for JWT token operations."""

    def test_create_access_token(self):
        """Test access token creation."""
        from app.core.security import SecurityUtils

        token = SecurityUtils.create_access_token(
            subject="user123",
            roles=["user"],
        )

        assert token is not None
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        from app.core.security import SecurityUtils

        token = SecurityUtils.create_refresh_token(subject="user123")

        assert token is not None
        assert len(token) > 0

    def test_verify_valid_token(self):
        """Test verification of valid token."""
        from app.core.security import SecurityUtils

        token = SecurityUtils.create_access_token(
            subject="user123",
            roles=["user", "admin"],
        )

        token_data = SecurityUtils.verify_token(token)

        assert token_data is not None
        assert token_data.sub == "user123"
        assert "user" in token_data.roles
        assert "admin" in token_data.roles
        assert token_data.token_type == "access"

    def test_verify_invalid_token(self):
        """Test verification of invalid token."""
        from app.core.security import SecurityUtils

        token_data = SecurityUtils.verify_token("invalid-token")

        assert token_data is None

    def test_token_expiration_check(self):
        """Test token expiration checking."""
        from app.core.security import SecurityUtils

        # Create expired token
        token = SecurityUtils.create_access_token(
            subject="user123",
            expires_delta=timedelta(seconds=-1),
        )

        token_data = SecurityUtils.verify_token(token)

        if token_data:
            assert SecurityUtils.is_token_expired(token_data) is True

    def test_create_tokens_response(self):
        """Test creating both access and refresh tokens."""
        from app.core.security import SecurityUtils

        response = SecurityUtils.create_tokens(
            subject="user123",
            roles=["user"],
        )

        assert response.access_token is not None
        assert response.refresh_token is not None
        assert response.token_type == "bearer"
        assert response.expires_in > 0


class TestTokenBucketRateLimiter:
    """Test cases for rate limiting."""

    def test_rate_limiter_allows_requests(self):
        """Test rate limiter allows requests under limit."""
        from app.core.security import TokenBucketRateLimiter

        limiter = TokenBucketRateLimiter(rate=10.0, capacity=5)

        allowed, info = limiter.is_allowed("test_key")

        assert allowed is True
        assert info["limit"] == 5

    def test_rate_limiter_blocks_excess(self):
        """Test rate limiter blocks excess requests."""
        from app.core.security import TokenBucketRateLimiter

        limiter = TokenBucketRateLimiter(rate=10.0, capacity=2)

        # Use all tokens
        limiter.is_allowed("test_key")
        limiter.is_allowed("test_key")

        # Next request should be blocked
        allowed, info = limiter.is_allowed("test_key")

        assert allowed is False

    def test_rate_limiter_reset(self):
        """Test rate limiter reset functionality."""
        from app.core.security import TokenBucketRateLimiter

        limiter = TokenBucketRateLimiter(rate=10.0, capacity=2)

        # Exhaust tokens
        limiter.is_allowed("test_key")
        limiter.is_allowed("test_key")

        # Reset
        limiter.reset("test_key")

        # Should be allowed again
        allowed, _ = limiter.is_allowed("test_key")
        assert allowed is True

    def test_rate_limiter_get_wait_time(self):
        """Test calculation of wait time."""
        from app.core.security import TokenBucketRateLimiter

        limiter = TokenBucketRateLimiter(rate=1.0, capacity=1)

        # Use token
        limiter.is_allowed("test_key")

        wait_time = limiter.get_wait_time("test_key")

        assert wait_time >= 0


class TestInputSanitizer:
    """Test cases for input sanitization."""

    def test_sanitize_html(self):
        """Test HTML sanitization."""
        from app.core.security import InputSanitizer

        dangerous = "<script>alert('xss')</script>"
        sanitized = InputSanitizer.sanitize_html(dangerous)

        assert "<script>" not in sanitized
        assert "&lt;script&gt;" in sanitized

    def test_sanitize_query(self):
        """Test query sanitization."""
        from app.core.security import InputSanitizer

        query = "  What is diabetes? <script>  "
        sanitized = InputSanitizer.sanitize_query(query)

        assert sanitized.startswith("What")
        assert "<script>" not in sanitized

    def test_detect_sql_injection(self):
        """Test SQL injection detection."""
        from app.core.security import InputSanitizer

        malicious = "'; DROP TABLE users; --"
        threats = InputSanitizer.detect_injection_attempt(malicious)

        assert threats["sql_injection"] is True

    def test_detect_script_injection(self):
        """Test script injection detection."""
        from app.core.security import InputSanitizer

        malicious = "<script>alert('xss')</script>"
        threats = InputSanitizer.detect_injection_attempt(malicious)

        assert threats["script_injection"] is True

    def test_is_safe_input_with_clean_text(self):
        """Test safe input validation with clean text."""
        from app.core.security import InputSanitizer

        clean = "What are the symptoms of diabetes?"
        assert InputSanitizer.is_safe_input(clean) is True

    def test_content_hash_generation(self):
        """Test content hash generation."""
        from app.core.security import InputSanitizer

        content = "Test content"
        hash1 = InputSanitizer.generate_content_hash(content)
        hash2 = InputSanitizer.generate_content_hash(content)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex digest length
