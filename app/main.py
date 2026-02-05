"""
Medical Chatbot API - Main Application

A production-ready FastAPI application for medical chatbot functionality.

Features:
- JWT authentication
- Rate limiting
- Prometheus metrics
- Structured logging
- MongoDB persistence
- Health checks
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes import auth_router, chat_router, health_router
from app.api.schemas import APIStatusResponse
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.db.mongodb import close_database, create_indexes, init_database
from app.middleware.request_handler import (
    ExceptionHandlerMiddleware,
    RequestContextMiddleware,
    SecurityHeadersMiddleware,
    setup_exception_handlers,
)


# Setup logging first
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment.value}")

    try:
        # Initialize database
        await init_database()
        await create_indexes()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization skipped: {str(e)}")

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application...")

    try:
        await close_database()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Error closing database: {str(e)}")

    logger.info("Application shutdown complete")


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.app_name,
        description="Production-ready Medical Chatbot API with RAG capabilities",
        version=settings.app_version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Add custom middleware (order matters - last added runs first)
    app.add_middleware(ExceptionHandlerMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestContextMiddleware)

    # Setup exception handlers
    setup_exception_handlers(app)

    # Include routers
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")

    # Root endpoint
    @app.get("/", response_model=APIStatusResponse, tags=["Status"])
    async def root() -> APIStatusResponse:
        """API root endpoint with status information."""
        return APIStatusResponse(
            name=settings.app_name,
            version=settings.app_version,
            status="operational",
            environment=settings.environment.value,
            documentation_url="/docs" if settings.debug else "Contact administrator",
        )

    # Mount static files for legacy Flask UI support
    try:
        app.mount("/static", StaticFiles(directory="static"), name="static")
    except RuntimeError:
        logger.warning("Static files directory not found")

    return app


# Create application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.workers,
        log_level=settings.log_level.lower(),
    )
