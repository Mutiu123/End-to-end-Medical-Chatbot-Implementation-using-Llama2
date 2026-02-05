"""
Centralized Configuration Management

This module provides type-safe configuration using Pydantic Settings.
Supports environment-specific configs (dev, staging, production).
Uses lru_cache for performance optimization.
"""

import os
from enum import Enum
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Application environment enumeration."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class Settings(BaseSettings):
    """
    Application settings with environment variable support.

    All settings can be overridden via environment variables.
    The .env file is automatically loaded if present.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application Settings
    app_name: str = Field(default="Medical Chatbot API", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Deployment environment"
    )
    debug: bool = Field(default=False, description="Enable debug mode")

    # Server Settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8080, description="Server port")
    workers: int = Field(default=4, description="Number of worker processes")

    # Security Settings
    secret_key: str = Field(
        default="change-this-in-production-use-strong-secret-key",
        description="Secret key for JWT encoding"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_minutes: int = Field(
        default=30,
        description="JWT token expiration in minutes"
    )
    jwt_refresh_expiration_days: int = Field(
        default=7,
        description="JWT refresh token expiration in days"
    )

    # CORS Settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(default=True, description="Allow credentials")
    cors_allow_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="Allowed HTTP methods"
    )
    cors_allow_headers: List[str] = Field(
        default=["*"],
        description="Allowed HTTP headers"
    )

    # Rate Limiting Settings
    rate_limit_requests: int = Field(
        default=100,
        description="Maximum requests per window"
    )
    rate_limit_window_seconds: int = Field(
        default=60,
        description="Rate limit window in seconds"
    )
    rate_limit_burst: int = Field(
        default=20,
        description="Burst capacity for token bucket"
    )

    # MongoDB Settings
    mongodb_uri: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection URI"
    )
    mongodb_database: str = Field(
        default="medical_chatbot",
        description="MongoDB database name"
    )
    mongodb_min_pool_size: int = Field(
        default=10,
        description="Minimum connection pool size"
    )
    mongodb_max_pool_size: int = Field(
        default=50,
        description="Maximum connection pool size"
    )
    mongodb_server_selection_timeout_ms: int = Field(
        default=5000,
        description="Server selection timeout in milliseconds"
    )
    mongodb_connect_timeout_ms: int = Field(
        default=10000,
        description="Connection timeout in milliseconds"
    )

    # Pinecone Settings
    pinecone_api_key: str = Field(
        default="",
        description="Pinecone API key"
    )
    pinecone_environment: str = Field(
        default="",
        description="Pinecone environment"
    )
    pinecone_index_name: str = Field(
        default="mchatbot",
        description="Pinecone index name"
    )

    # LLM Settings
    llm_model_path: str = Field(
        default="model/llama-2-7b-chat.ggmlv3.q4_0.bin",
        description="Path to LLM model file"
    )
    llm_model_type: str = Field(default="llama", description="LLM model type")
    llm_max_tokens: int = Field(default=512, description="Maximum tokens for response")
    llm_temperature: float = Field(default=0.7, description="LLM temperature")
    llm_context_length: int = Field(default=2048, description="Context length")

    # Logging Settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")
    log_file_path: Optional[str] = Field(
        default=None,
        description="Optional log file path"
    )

    # Prometheus Metrics Settings
    metrics_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_prefix: str = Field(
        default="medical_chatbot",
        description="Metrics prefix"
    )

    # Health Check Settings
    health_check_path: str = Field(default="/health", description="Health check path")
    readiness_check_path: str = Field(
        default="/ready",
        description="Readiness check path"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("environment", mode="before")
    @classmethod
    def parse_environment(cls, v):
        """Parse environment string to enum."""
        if isinstance(v, str):
            return Environment(v.lower())
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == Environment.TESTING


class DevelopmentSettings(Settings):
    """Development-specific settings."""

    debug: bool = True
    log_level: str = "DEBUG"
    rate_limit_requests: int = 1000


class StagingSettings(Settings):
    """Staging-specific settings."""

    debug: bool = False
    log_level: str = "INFO"


class ProductionSettings(Settings):
    """Production-specific settings with stricter defaults."""

    debug: bool = False
    log_level: str = "WARNING"
    cors_origins: List[str] = Field(default_factory=list)


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings based on environment.

    Uses lru_cache to ensure settings are loaded only once.
    Returns environment-specific settings class.
    """
    env = os.getenv("ENVIRONMENT", "development").lower()

    settings_map = {
        "development": DevelopmentSettings,
        "staging": StagingSettings,
        "production": ProductionSettings,
        "testing": Settings,
    }

    settings_class = settings_map.get(env, Settings)
    return settings_class()


# Global settings instance
settings = get_settings()
