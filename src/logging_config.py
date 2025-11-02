"""Structured logging configuration for MS2 QBank services.

This module provides production-ready structured logging with:
- JSON formatting for log aggregation (ELK, Splunk, etc.)
- Correlation IDs for request tracing
- Sensitive data masking
- Different log levels per environment
- Request/response logging middleware
"""

from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


# Context variable for correlation ID (thread-safe)
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging.

    Outputs log records as JSON with standard fields:
    - timestamp: ISO 8601 timestamp
    - level: Log level (INFO, ERROR, etc.)
    - logger: Logger name
    - message: Log message
    - correlation_id: Request correlation ID (if available)
    - extra: Additional context fields
    """

    SENSITIVE_KEYS = {
        "password",
        "token",
        "secret",
        "api_key",
        "authorization",
        "jwt",
        "refresh_token",
        "access_token",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Base log entry
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add correlation ID if available
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_data["correlation_id"] = correlation_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        # Add extra fields (mask sensitive data)
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in ("name", "msg", "args", "created", "filename", "funcName",
                               "levelname", "levelno", "lineno", "module", "msecs",
                               "message", "pathname", "process", "processName",
                               "relativeCreated", "thread", "threadName", "exc_info",
                               "exc_text", "stack_info"):
                    # Mask sensitive values
                    if key.lower() in self.SENSITIVE_KEYS:
                        log_data[key] = "***REDACTED***"
                    else:
                        log_data[key] = self._sanitize_value(value)

        return json.dumps(log_data, default=str)

    def _sanitize_value(self, value: Any) -> Any:
        """Sanitize log values to remove sensitive data."""
        if isinstance(value, dict):
            return {
                k: "***REDACTED***" if k.lower() in self.SENSITIVE_KEYS else self._sanitize_value(v)
                for k, v in value.items()
            }
        elif isinstance(value, (list, tuple)):
            return [self._sanitize_value(item) for item in value]
        elif isinstance(value, str) and len(value) > 1000:
            # Truncate very long strings
            return value[:1000] + "...[truncated]"
        return value


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses with structured logging.

    Features:
    - Generates correlation ID for each request
    - Logs request details (method, path, headers)
    - Logs response details (status, duration)
    - Masks sensitive headers (Authorization, etc.)
    """

    SENSITIVE_HEADERS = {"authorization", "cookie", "x-api-key"}

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request and log details."""
        # Generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        correlation_id_var.set(correlation_id)

        # Start timer
        start_time = time.time()

        # Log incoming request
        logger = logging.getLogger("http.request")
        logger.info(
            "Incoming request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": self._mask_headers(dict(request.headers)),
                "client_ip": request.client.host if request.client else None,
            },
        )

        # Process request
        try:
            response = await call_next(request)
        except Exception as exc:
            # Log exception
            duration = time.time() - start_time
            logger.error(
                "Request failed with exception",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration * 1000, 2),
                },
                exc_info=True,
            )
            raise

        # Calculate duration
        duration = time.time() - start_time

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        # Log response
        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            },
        )

        # Clear correlation ID
        correlation_id_var.set(None)

        return response

    def _mask_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Mask sensitive header values."""
        return {
            key: "***REDACTED***" if key.lower() in self.SENSITIVE_HEADERS else value
            for key, value in headers.items()
        }


def configure_logging(
    level: str = "INFO",
    service_name: str = "ms2-qbank",
    json_format: bool = True,
) -> None:
    """Configure structured logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        service_name: Name of the service for log tagging
        json_format: Whether to use JSON formatting (True for production)

    Example:
        >>> from logging_config import configure_logging
        >>> configure_logging(level="INFO", service_name="users-api")
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("User logged in", extra={"user_id": 123})
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    root_logger.handlers = []

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    # Set formatter
    if json_format:
        formatter = StructuredFormatter()
    else:
        # Simple format for development
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set service name in all logs
    logging.root.name = service_name

    # Configure third-party library log levels
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Log configuration
    root_logger.info(
        "Logging configured",
        extra={
            "level": level,
            "service": service_name,
            "json_format": json_format,
        },
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started", extra={"job_id": "abc123"})
    """
    return logging.getLogger(name)


__all__ = [
    "configure_logging",
    "get_logger",
    "StructuredFormatter",
    "RequestLoggingMiddleware",
    "correlation_id_var",
]
