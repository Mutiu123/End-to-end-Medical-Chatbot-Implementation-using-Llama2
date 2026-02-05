"""
MongoDB Connection Management

Implements:
- Singleton pattern for connection sharing
- Connection pooling (min 10, max 50)
- Health checks and timeouts
- Graceful connection closure
"""

import asyncio
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings
from app.core.logging import get_logger
from app.core.metrics import metrics


logger = get_logger(__name__)


class MongoDBManager:
    """
    MongoDB connection manager implementing singleton pattern.

    Manages connection pooling and provides centralized
    database access across the application.
    """

    _instance: Optional["MongoDBManager"] = None
    _client: Optional[AsyncIOMotorClient] = None
    _database: Optional[AsyncIOMotorDatabase] = None
    _initialized: bool = False

    def __new__(cls) -> "MongoDBManager":
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self) -> None:
        """
        Initialize MongoDB connection with pooling.

        Configures:
        - Min pool size: 10 connections
        - Max pool size: 50 connections
        - Server selection timeout: 5 seconds
        - Connection timeout: 10 seconds
        """
        if self._initialized:
            logger.debug("MongoDB already initialized")
            return

        try:
            logger.info("Initializing MongoDB connection...")

            self._client = AsyncIOMotorClient(
                settings.mongodb_uri,
                minPoolSize=settings.mongodb_min_pool_size,
                maxPoolSize=settings.mongodb_max_pool_size,
                serverSelectionTimeoutMS=settings.mongodb_server_selection_timeout_ms,
                connectTimeoutMS=settings.mongodb_connect_timeout_ms,
                retryWrites=True,
                retryReads=True,
            )

            self._database = self._client[settings.mongodb_database]

            # Verify connection
            await self._client.admin.command("ping")

            self._initialized = True
            logger.info(
                f"MongoDB connected successfully to database: {settings.mongodb_database}"
            )

            # Update metrics
            metrics.db_connections.labels(state="active").set(
                settings.mongodb_min_pool_size
            )
            metrics.health_check_status.labels(component="database").set(1)

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            metrics.health_check_status.labels(component="database").set(0)
            raise

    async def close(self) -> None:
        """
        Gracefully close MongoDB connection.

        Ensures all pending operations complete before closing.
        """
        if self._client is not None:
            logger.info("Closing MongoDB connection...")
            self._client.close()
            self._client = None
            self._database = None
            self._initialized = False
            metrics.db_connections.labels(state="active").set(0)
            logger.info("MongoDB connection closed")

    @property
    def client(self) -> AsyncIOMotorClient:
        """Get MongoDB client instance."""
        if self._client is None:
            raise RuntimeError("MongoDB not initialized. Call initialize() first.")
        return self._client

    @property
    def database(self) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if self._database is None:
            raise RuntimeError("MongoDB not initialized. Call initialize() first.")
        return self._database

    async def health_check(self) -> bool:
        """
        Perform database health check.

        Returns:
            True if database is healthy, False otherwise
        """
        if not self._initialized or self._client is None:
            return False

        try:
            await asyncio.wait_for(
                self._client.admin.command("ping"),
                timeout=5.0
            )
            return True
        except Exception as e:
            logger.warning(f"Database health check failed: {str(e)}")
            return False

    async def get_stats(self) -> dict:
        """
        Get database connection statistics.

        Returns:
            Dictionary with connection stats
        """
        if not self._initialized or self._client is None:
            return {"status": "not_connected"}

        try:
            server_info = await self._client.server_info()
            return {
                "status": "connected",
                "version": server_info.get("version"),
                "database": settings.mongodb_database,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


# Global manager instance
_db_manager = MongoDBManager()


async def init_database() -> None:
    """Initialize database connection."""
    await _db_manager.initialize()


async def get_database() -> AsyncIOMotorDatabase:
    """
    Get database instance.

    Ensures connection is initialized before returning.

    Returns:
        AsyncIOMotorDatabase instance
    """
    if not _db_manager._initialized:
        await _db_manager.initialize()
    return _db_manager.database


async def close_database() -> None:
    """Close database connection."""
    await _db_manager.close()


async def check_database_health() -> bool:
    """
    Check database health.

    Returns:
        True if healthy, False otherwise
    """
    return await _db_manager.health_check()


async def create_indexes() -> None:
    """
    Create database indexes for optimal query performance.

    Called during application startup.
    """
    try:
        db = await get_database()

        # Users collection indexes
        users = db["users"]
        await users.create_index("username", unique=True)
        await users.create_index("email", unique=True)
        await users.create_index("created_at")

        # Conversations collection indexes
        conversations = db["conversations"]
        await conversations.create_index("session_id", unique=True)
        await conversations.create_index("user_id")
        await conversations.create_index("created_at")
        await conversations.create_index("updated_at")

        # Audit logs collection indexes
        audit_logs = db["audit_logs"]
        await audit_logs.create_index("timestamp")
        await audit_logs.create_index("user_id")
        await audit_logs.create_index("event_type")
        await audit_logs.create_index([("timestamp", -1)], expireAfterSeconds=7776000)  # 90 days TTL

        logger.info("Database indexes created successfully")

    except Exception as e:
        logger.error(f"Failed to create database indexes: {str(e)}")
        raise
