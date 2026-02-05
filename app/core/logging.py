"""
Structured Logging Module

Provides JSON-formatted logging with:
- Request ID tracking
- Custom formatters
- Audit logging
- Performance metrics
"""

import json
import logging
import sys
import traceback
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.core.config import settings


# Context variable for request ID tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Outputs logs in JSON format for easy parsing by log aggregation systems.
    """

    def __init__(self, **kwargs):
        super().__init__()
        self.default_fields = kwargs

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request ID if available
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        # Add default fields
        log_data.update(self.default_fields)

        # Add extra fields from record
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_data, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter for development."""

    def __init__(self):
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as readable text."""
        # Add request ID prefix if available
        request_id = request_id_var.get()
        if request_id:
            record.msg = f"[{request_id[:8]}] {record.msg}"

        return super().format(record)


class ContextLogger(logging.LoggerAdapter):
    """
    Logger adapter that automatically includes context information.

    Provides methods for logging with additional structured data.
    """

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process log message with context data."""
        extra = kwargs.get("extra", {})

        # Add request ID
        request_id = request_id_var.get()
        if request_id:
            extra["request_id"] = request_id

        kwargs["extra"] = extra
        return msg, kwargs

    def with_data(self, **data) -> "ContextLogger":
        """Create a logger with additional context data."""
        new_extra = {**self.extra, **data}
        return ContextLogger(self.logger, new_extra)


class AuditLogger:
    """
    Specialized logger for audit events.

    Logs security-relevant events with structured data for compliance.
    """

    def __init__(self, name: str = "audit"):
        self.logger = logging.getLogger(f"medical_chatbot.{name}")

    def log_event(
        self,
        event_type: str,
        action: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
    ) -> None:
        """
        Log an audit event.

        Args:
            event_type: Type of event (auth, access, modification, etc.)
            action: Specific action performed
            user_id: ID of user performing action
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            details: Additional event details
            success: Whether action succeeded
        """
        audit_data = {
            "event_type": event_type,
            "action": action,
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if user_id:
            audit_data["user_id"] = user_id
        if resource_type:
            audit_data["resource_type"] = resource_type
        if resource_id:
            audit_data["resource_id"] = resource_id
        if details:
            audit_data["details"] = details

        request_id = request_id_var.get()
        if request_id:
            audit_data["request_id"] = request_id

        level = logging.INFO if success else logging.WARNING
        self.logger.log(level, f"AUDIT: {event_type}.{action}", extra={"extra_data": audit_data})

    def log_authentication(
        self,
        user_id: str,
        action: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log authentication events."""
        self.log_event(
            event_type="authentication",
            action=action,
            user_id=user_id,
            success=success,
            details=details,
        )

    def log_prediction(
        self,
        user_id: Optional[str],
        query: str,
        response_length: int,
        latency_ms: float,
        success: bool,
    ) -> None:
        """Log prediction/chat events."""
        self.log_event(
            event_type="prediction",
            action="chat_query",
            user_id=user_id,
            success=success,
            details={
                "query_length": len(query),
                "response_length": response_length,
                "latency_ms": latency_ms,
            },
        )

    def log_access(
        self,
        user_id: Optional[str],
        resource_type: str,
        resource_id: str,
        action: str,
        success: bool,
    ) -> None:
        """Log resource access events."""
        self.log_event(
            event_type="access",
            action=action,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            success=success,
        )


def setup_logging() -> None:
    """
    Configure application logging.

    Sets up formatters, handlers, and log levels based on configuration.
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Remove existing handlers
    root_logger.handlers = []

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level.upper()))

    # Choose formatter based on config
    if settings.log_format == "json":
        formatter = JSONFormatter(
            app_name=settings.app_name,
            environment=settings.environment.value,
        )
    else:
        formatter = TextFormatter()

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Add file handler if configured
    if settings.log_file_path:
        file_handler = logging.FileHandler(settings.log_file_path)
        file_handler.setLevel(getattr(logging, settings.log_level.upper()))
        file_handler.setFormatter(JSONFormatter(
            app_name=settings.app_name,
            environment=settings.environment.value,
        ))
        root_logger.addHandler(file_handler)

    # Set log levels for noisy libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> ContextLogger:
    """
    Get a context-aware logger.

    Args:
        name: Logger name (typically __name__)

    Returns:
        ContextLogger instance
    """
    logger = logging.getLogger(f"medical_chatbot.{name}")
    return ContextLogger(logger, {})


# Initialize audit logger
audit_logger = AuditLogger()
