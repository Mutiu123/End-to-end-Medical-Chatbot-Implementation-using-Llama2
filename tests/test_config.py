"""
Tests for Configuration Module

Tests configuration loading, environment handling,
and settings validation.
"""

import os
from unittest.mock import patch

import pytest


class TestSettings:
    """Test cases for Settings class."""

    def test_default_settings(self):
        """Test default settings values."""
        from app.core.config import Settings

        settings = Settings()

        assert settings.app_name == "Medical Chatbot API"
        assert settings.app_version == "1.0.0"
        assert settings.debug is False
        assert settings.host == "0.0.0.0"
        assert settings.port == 8080

    def test_environment_parsing(self):
        """Test environment enumeration parsing."""
        from app.core.config import Environment, Settings

        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            settings = Settings()
            assert settings.environment == Environment.PRODUCTION

    def test_cors_origins_from_string(self):
        """Test CORS origins parsing from comma-separated string."""
        from app.core.config import Settings

        with patch.dict(os.environ, {"CORS_ORIGINS": "http://localhost:3000,http://localhost:8080"}):
            settings = Settings()
            assert "http://localhost:3000" in settings.cors_origins
            assert "http://localhost:8080" in settings.cors_origins

    def test_is_production_property(self):
        """Test is_production property."""
        from app.core.config import Environment, Settings

        settings = Settings()
        settings.environment = Environment.PRODUCTION
        assert settings.is_production is True

        settings.environment = Environment.DEVELOPMENT
        assert settings.is_production is False

    def test_is_development_property(self):
        """Test is_development property."""
        from app.core.config import Environment, Settings

        settings = Settings()
        settings.environment = Environment.DEVELOPMENT
        assert settings.is_development is True

    def test_mongodb_settings(self):
        """Test MongoDB configuration settings."""
        from app.core.config import Settings

        settings = Settings()

        assert settings.mongodb_min_pool_size == 10
        assert settings.mongodb_max_pool_size == 50
        assert settings.mongodb_server_selection_timeout_ms == 5000
        assert settings.mongodb_connect_timeout_ms == 10000

    def test_rate_limit_settings(self):
        """Test rate limiting configuration."""
        from app.core.config import Settings

        settings = Settings()

        assert settings.rate_limit_requests == 100
        assert settings.rate_limit_window_seconds == 60
        assert settings.rate_limit_burst == 20

    def test_jwt_settings(self):
        """Test JWT configuration."""
        from app.core.config import Settings

        settings = Settings()

        assert settings.jwt_algorithm == "HS256"
        assert settings.jwt_expiration_minutes == 30
        assert settings.jwt_refresh_expiration_days == 7


class TestGetSettings:
    """Test cases for get_settings function."""

    def test_get_settings_caching(self):
        """Test that settings are cached with lru_cache."""
        from app.core.config import get_settings

        # Clear cache first
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_development_settings(self):
        """Test development-specific settings."""
        from app.core.config import get_settings

        get_settings.cache_clear()

        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            from app.core.config import DevelopmentSettings
            settings = DevelopmentSettings()
            assert settings.debug is True
            assert settings.log_level == "DEBUG"

    def test_production_settings(self):
        """Test production-specific settings."""
        from app.core.config import ProductionSettings

        settings = ProductionSettings()
        assert settings.debug is False
        assert settings.log_level == "WARNING"
