# =============================================================================
# Production Dockerfile for Medical Chatbot API
# Multi-stage build for optimized image size and security
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies and build wheels
# -----------------------------------------------------------------------------
FROM python:3.11-slim as builder

# Set build arguments
ARG DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-prod.txt

# -----------------------------------------------------------------------------
# Stage 2: Production - Final optimized image
# -----------------------------------------------------------------------------
FROM python:3.11-slim as production

# Labels for container metadata
LABEL maintainer="Medical Chatbot Team" \
      version="1.0.0" \
      description="Production Medical Chatbot API" \
      org.opencontainers.image.source="https://github.com/Mutiu123/End-to-end-Medical-Chatbot-Implementation-using-Llama2"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_HOME=/app \
    ENVIRONMENT=production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR ${APP_HOME}

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=appuser:appgroup app/ ${APP_HOME}/app/
COPY --chown=appuser:appgroup src/ ${APP_HOME}/src/
COPY --chown=appuser:appgroup templates/ ${APP_HOME}/templates/
COPY --chown=appuser:appgroup static/ ${APP_HOME}/static/

# Create necessary directories
RUN mkdir -p ${APP_HOME}/logs ${APP_HOME}/model && \
    chown -R appuser:appgroup ${APP_HOME}

# Switch to non-root user
USER appuser

# Expose application port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/v1/live || exit 1

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
