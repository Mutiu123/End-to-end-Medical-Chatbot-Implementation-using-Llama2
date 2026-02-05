"""
Security Module

Implements comprehensive security features:
- JWT token generation and verification
- Password hashing with bcrypt
- Token bucket rate limiting algorithm
- Input sanitization
- Security headers middleware
"""

import hashlib
import html
import re
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings


class TokenData(BaseModel):
    """JWT token payload data model."""

    sub: str
    exp: datetime
    iat: datetime
    jti: str
    token_type: str = "access"
    roles: list[str] = []


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class SecurityUtils:
    """Security utility functions for authentication and authorization."""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password string
        """
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Stored hashed password

        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )

    @staticmethod
    def generate_token_id() -> str:
        """Generate a unique token ID (JTI)."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_access_token(
        subject: str,
        roles: list[str] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.

        Args:
            subject: Token subject (usually user ID)
            roles: List of user roles
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT token string
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=settings.jwt_expiration_minutes)

        now = datetime.now(timezone.utc)
        expire = now + expires_delta

        payload = {
            "sub": subject,
            "exp": expire,
            "iat": now,
            "jti": SecurityUtils.generate_token_id(),
            "token_type": "access",
            "roles": roles or [],
        }

        return jwt.encode(
            payload,
            settings.secret_key,
            algorithm=settings.jwt_algorithm
        )

    @staticmethod
    def create_refresh_token(subject: str) -> str:
        """
        Create a JWT refresh token.

        Args:
            subject: Token subject (usually user ID)

        Returns:
            Encoded JWT refresh token string
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=settings.jwt_refresh_expiration_days)

        payload = {
            "sub": subject,
            "exp": expire,
            "iat": now,
            "jti": SecurityUtils.generate_token_id(),
            "token_type": "refresh",
        }

        return jwt.encode(
            payload,
            settings.secret_key,
            algorithm=settings.jwt_algorithm
        )

    @staticmethod
    def create_tokens(subject: str, roles: list[str] = None) -> TokenResponse:
        """
        Create both access and refresh tokens.

        Args:
            subject: Token subject (usually user ID)
            roles: List of user roles

        Returns:
            TokenResponse with both tokens
        """
        access_token = SecurityUtils.create_access_token(subject, roles)
        refresh_token = SecurityUtils.create_refresh_token(subject)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.jwt_expiration_minutes * 60
        )

    @staticmethod
    def verify_token(token: str) -> Optional[TokenData]:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token string

        Returns:
            TokenData if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.jwt_algorithm]
            )

            return TokenData(
                sub=payload.get("sub"),
                exp=datetime.fromtimestamp(payload.get("exp"), tz=timezone.utc),
                iat=datetime.fromtimestamp(payload.get("iat"), tz=timezone.utc),
                jti=payload.get("jti"),
                token_type=payload.get("token_type", "access"),
                roles=payload.get("roles", []),
            )
        except JWTError:
            return None

    @staticmethod
    def is_token_expired(token_data: TokenData) -> bool:
        """Check if a token has expired."""
        return datetime.now(timezone.utc) > token_data.exp


class TokenBucketRateLimiter:
    """
    Token bucket algorithm implementation for rate limiting.

    This implementation provides burst capacity while maintaining
    a sustained rate limit over time.
    """

    def __init__(
        self,
        rate: float,
        capacity: int,
        storage: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the rate limiter.

        Args:
            rate: Tokens added per second
            capacity: Maximum bucket capacity (burst limit)
            storage: Optional external storage for distributed systems
        """
        self.rate = rate
        self.capacity = capacity
        self._buckets: Dict[str, Dict[str, float]] = storage or {}

    def _get_bucket(self, key: str) -> Dict[str, float]:
        """Get or create a bucket for the given key."""
        if key not in self._buckets:
            self._buckets[key] = {
                "tokens": float(self.capacity),
                "last_update": time.time()
            }
        return self._buckets[key]

    def _refill_tokens(self, bucket: Dict[str, float]) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - bucket["last_update"]
        tokens_to_add = elapsed * self.rate
        bucket["tokens"] = min(self.capacity, bucket["tokens"] + tokens_to_add)
        bucket["last_update"] = now

    def is_allowed(self, key: str, tokens: int = 1) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if a request is allowed under rate limiting.

        Args:
            key: Identifier for the rate limit bucket (e.g., IP address)
            tokens: Number of tokens to consume

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        bucket = self._get_bucket(key)
        self._refill_tokens(bucket)

        info = {
            "limit": self.capacity,
            "remaining": int(bucket["tokens"]),
            "reset": int(bucket["last_update"] + (self.capacity / self.rate)),
        }

        if bucket["tokens"] >= tokens:
            bucket["tokens"] -= tokens
            info["remaining"] = int(bucket["tokens"])
            return True, info

        return False, info

    def get_wait_time(self, key: str, tokens: int = 1) -> float:
        """
        Calculate wait time until tokens are available.

        Args:
            key: Identifier for the rate limit bucket
            tokens: Number of tokens needed

        Returns:
            Wait time in seconds
        """
        bucket = self._get_bucket(key)
        self._refill_tokens(bucket)

        if bucket["tokens"] >= tokens:
            return 0.0

        tokens_needed = tokens - bucket["tokens"]
        return tokens_needed / self.rate

    def reset(self, key: str) -> None:
        """Reset the bucket for a given key."""
        if key in self._buckets:
            del self._buckets[key]


class InputSanitizer:
    """
    Input sanitization utilities to prevent injection attacks.

    Provides methods for sanitizing various types of user input.
    """

    # Patterns for detecting potential injection attacks
    SQL_INJECTION_PATTERN = re.compile(
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b)",
        re.IGNORECASE
    )

    SCRIPT_INJECTION_PATTERN = re.compile(
        r"<script[^>]*>.*?</script>",
        re.IGNORECASE | re.DOTALL
    )

    COMMAND_INJECTION_PATTERN = re.compile(
        r"[;&|`$()]",
        re.IGNORECASE
    )

    @staticmethod
    def sanitize_html(text: str) -> str:
        """
        Escape HTML special characters.

        Args:
            text: Input text to sanitize

        Returns:
            HTML-escaped text
        """
        return html.escape(text, quote=True)

    @staticmethod
    def sanitize_for_logging(text: str) -> str:
        """
        Sanitize text for safe logging.

        Args:
            text: Input text to sanitize

        Returns:
            Sanitized text safe for logging
        """
        # Remove control characters
        sanitized = "".join(
            char for char in text
            if ord(char) >= 32 or char in "\n\r\t"
        )
        # Truncate long strings
        max_length = 1000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "...[truncated]"
        return sanitized

    @staticmethod
    def sanitize_query(query: str) -> str:
        """
        Sanitize user query input for the chatbot.

        Args:
            query: User's chat query

        Returns:
            Sanitized query string
        """
        # Strip leading/trailing whitespace
        sanitized = query.strip()

        # Remove null bytes
        sanitized = sanitized.replace("\x00", "")

        # Escape HTML entities
        sanitized = html.escape(sanitized, quote=True)

        # Limit length
        max_length = 2000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized

    @staticmethod
    def detect_injection_attempt(text: str) -> Dict[str, bool]:
        """
        Detect potential injection attacks in input.

        Args:
            text: Input text to analyze

        Returns:
            Dictionary indicating detected threat types
        """
        return {
            "sql_injection": bool(
                InputSanitizer.SQL_INJECTION_PATTERN.search(text)
            ),
            "script_injection": bool(
                InputSanitizer.SCRIPT_INJECTION_PATTERN.search(text)
            ),
            "command_injection": bool(
                InputSanitizer.COMMAND_INJECTION_PATTERN.search(text)
            ),
        }

    @staticmethod
    def is_safe_input(text: str) -> bool:
        """
        Check if input is safe from common injection attacks.

        Args:
            text: Input text to check

        Returns:
            True if input appears safe, False otherwise
        """
        threats = InputSanitizer.detect_injection_attempt(text)
        return not any(threats.values())

    @staticmethod
    def generate_content_hash(content: str) -> str:
        """
        Generate a SHA-256 hash of content for integrity verification.

        Args:
            content: Content to hash

        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()


# Global rate limiter instance
rate_limiter = TokenBucketRateLimiter(
    rate=settings.rate_limit_requests / settings.rate_limit_window_seconds,
    capacity=settings.rate_limit_burst
)
