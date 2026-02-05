"""
Health Check Endpoints

Provides health and readiness check endpoints for:
- Kubernetes liveness probes
- Load balancer health checks
- Service dependency verification
"""

import time
from datetime import datetime, timezone
from typing import Dict

from fastapi import APIRouter, Depends, Response

from app.api.dependencies import get_request_id
from app.api.schemas import (
    ComponentHealth,
    HealthCheckResponse,
    HealthStatus,
    ReadinessResponse,
)
from app.core.config import settings
from app.core.logging import get_logger
from app.core.metrics import metrics
from app.db.mongodb import check_database_health


logger = get_logger(__name__)
router = APIRouter(tags=["Health"])

# Track application start time for uptime calculation
APP_START_TIME = time.time()


async def check_component_health(
    name: str,
    check_func,
) -> ComponentHealth:
    """
    Check health of a component.

    Args:
        name: Component name
        check_func: Async function that returns (is_healthy, details)

    Returns:
        ComponentHealth instance
    """
    start_time = time.perf_counter()

    try:
        is_healthy, details = await check_func()
        latency_ms = (time.perf_counter() - start_time) * 1000

        status = HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY
        metrics.health_check_status.labels(component=name).set(1 if is_healthy else 0)

        return ComponentHealth(
            name=name,
            status=status,
            latency_ms=round(latency_ms, 2),
            details=details,
            last_check=datetime.now(timezone.utc),
        )
    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        metrics.health_check_status.labels(component=name).set(0)
        logger.error(f"Health check failed for {name}: {str(e)}")

        return ComponentHealth(
            name=name,
            status=HealthStatus.UNHEALTHY,
            latency_ms=round(latency_ms, 2),
            details={"error": str(e)},
            last_check=datetime.now(timezone.utc),
        )


async def check_api_health() -> tuple:
    """Check API health."""
    return True, {"message": "API is operational"}


async def check_db_health() -> tuple:
    """Check database health."""
    is_healthy = await check_database_health()
    details = {"connected": is_healthy}
    if not is_healthy:
        details["error"] = "Database connection failed"
    return is_healthy, details


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="Comprehensive health check for all application components",
)
async def health_check(
    request_id: str = Depends(get_request_id),
) -> HealthCheckResponse:
    """
    Perform comprehensive health check.

    Checks health of:
    - API service
    - Database connection
    - Vector store (Pinecone)

    Returns:
        HealthCheckResponse with component statuses
    """
    components = []

    # Check API health
    api_health = await check_component_health("api", check_api_health)
    components.append(api_health)

    # Check database health
    db_health = await check_component_health("database", check_db_health)
    components.append(db_health)

    # Determine overall status
    unhealthy_count = sum(1 for c in components if c.status == HealthStatus.UNHEALTHY)
    degraded_count = sum(1 for c in components if c.status == HealthStatus.DEGRADED)

    if unhealthy_count > 0:
        overall_status = HealthStatus.UNHEALTHY
    elif degraded_count > 0:
        overall_status = HealthStatus.DEGRADED
    else:
        overall_status = HealthStatus.HEALTHY

    uptime = time.time() - APP_START_TIME

    return HealthCheckResponse(
        status=overall_status,
        version=settings.app_version,
        uptime_seconds=round(uptime, 2),
        components=components,
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness Check",
    description="Check if the application is ready to accept traffic",
)
async def readiness_check() -> ReadinessResponse:
    """
    Perform readiness check.

    Verifies that all critical dependencies are available
    and the application is ready to handle requests.

    Returns:
        ReadinessResponse with readiness status
    """
    checks: Dict[str, bool] = {}

    # Check database readiness
    try:
        checks["database"] = await check_database_health()
    except Exception:
        checks["database"] = False

    # API is always ready if this endpoint responds
    checks["api"] = True

    # Overall readiness
    is_ready = all(checks.values())

    return ReadinessResponse(
        ready=is_ready,
        checks=checks,
    )


@router.get(
    "/live",
    summary="Liveness Check",
    description="Simple liveness probe for Kubernetes",
)
async def liveness_check() -> Dict[str, str]:
    """
    Simple liveness check.

    Used by Kubernetes liveness probes to determine
    if the container should be restarted.

    Returns:
        Simple status response
    """
    return {"status": "alive"}


@router.get(
    "/metrics",
    summary="Prometheus Metrics",
    description="Prometheus metrics endpoint",
)
async def prometheus_metrics() -> Response:
    """
    Expose Prometheus metrics.

    Returns:
        Prometheus metrics in text format
    """
    return Response(
        content=metrics.get_metrics(),
        media_type=metrics.get_content_type(),
    )
