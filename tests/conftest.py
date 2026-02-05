"""
Pytest Configuration and Fixtures

Provides shared fixtures for all test modules.
"""

import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Set test environment before importing app
os.environ["ENVIRONMENT"] = "testing"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017"
os.environ["MONGODB_DATABASE"] = "medical_chatbot_test"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["PINECONE_API_KEY"] = "test-pinecone-key"
os.environ["DEBUG"] = "true"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB connection."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock(return_value=None)
    mock_collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id="test_id"))
    mock_collection.update_one = AsyncMock()
    mock_collection.delete_one = AsyncMock()
    mock_collection.create_index = AsyncMock()
    mock_db.__getitem__ = MagicMock(return_value=mock_collection)
    return mock_db


@pytest.fixture
def app(mock_mongodb):
    """Create test application instance."""
    with patch("app.db.mongodb._db_manager._initialized", True), \
         patch("app.db.mongodb._db_manager._database", mock_mongodb), \
         patch("app.db.mongodb.check_database_health", AsyncMock(return_value=True)):
        from app.main import create_application
        test_app = create_application()
        yield test_app


@pytest.fixture
def client(app) -> Generator:
    """Create synchronous test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client(app) -> AsyncGenerator:
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_user_data():
    """Sample user registration data."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User",
    }


@pytest.fixture
def sample_chat_request():
    """Sample chat request data."""
    return {
        "query": "What are the symptoms of diabetes?",
        "session_id": "test-session-123",
        "include_sources": False,
    }


@pytest.fixture
def valid_token():
    """Generate a valid JWT token for testing."""
    from app.core.security import SecurityUtils
    return SecurityUtils.create_access_token(
        subject="test_user_id",
        roles=["user"],
    )


@pytest.fixture
def admin_token():
    """Generate an admin JWT token for testing."""
    from app.core.security import SecurityUtils
    return SecurityUtils.create_access_token(
        subject="admin_user_id",
        roles=["admin", "user"],
    )


@pytest.fixture
def expired_token():
    """Generate an expired JWT token for testing."""
    from datetime import timedelta
    from app.core.security import SecurityUtils
    return SecurityUtils.create_access_token(
        subject="test_user_id",
        roles=["user"],
        expires_delta=timedelta(seconds=-1),
    )


@pytest.fixture
def mock_chatbot_service():
    """Mock chatbot service."""
    mock_service = MagicMock()
    mock_service.process_query = AsyncMock(return_value={
        "response": "Test response from chatbot",
        "session_id": "test-session",
        "sources": [],
    })
    mock_service.is_initialized = True
    return mock_service
