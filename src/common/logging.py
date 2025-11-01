"""Centralized logging configuration for all microservices.

This module provides:
- Structured JSON logging with loguru
- Sentry integration for error tracking
- Request/response logging middleware
- Correlation IDs for request tracing
"""

import os
import sys
import time
import uuid
from typing import Optional

import sentry_sdk
from fastapi import FastAPI, Request, Response
from loguru import logger
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from starlette.middleware.base import BaseHTTPMiddleware


# Environment variables
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
SENTRY_DSN = os.getenv("SENTRY_DSN", None)
SERVICE_NAME = os.getenv("SERVICE_NAME", "ms2qbank")


def setup_logging(service_name: str = SERVICE_NAME, log_level: str = LOG_LEVEL) -> None:
    """Configure structured logging with loguru.

    Args:
        service_name: Name of the microservice (e.g., "users", "flashcards")
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Remove default logger
    logger.remove()

    # Add console logger with structured format
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    # Add JSON logger for production
    if ENVIRONMENT == "production":
        logger.add(
            f"logs/{service_name}.json",
            format="{time} {level} {message}",
            level=log_level,
            rotation="500 MB",
            retention="10 days",
            compression="zip",
            serialize=True,  # JSON format
        )

    # Add extra context
    logger.configure(
        extra={
            "service": service_name,
            "environment": ENVIRONMENT,
        }
    )

    logger.info(
        f"Logging initialized for {service_name}",
        service=service_name,
        log_level=log_level,
        environment=ENVIRONMENT,
    )


def setup_sentry(
    service_name: str = SERVICE_NAME,
    dsn: Optional[str] = SENTRY_DSN,
    traces_sample_rate: float = 0.1,
) -> None:
    """Configure Sentry for error tracking and performance monitoring.

    Args:
        service_name: Name of the microservice
        dsn: Sentry DSN (Data Source Name)
        traces_sample_rate: Percentage of transactions to sample (0.0 to 1.0)
    """
    if not dsn:
        logger.warning(
            "Sentry DSN not configured. Error tracking disabled.",
            service=service_name,
        )
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=ENVIRONMENT,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=traces_sample_rate,
        send_default_pii=False,  # Don't send personally identifiable information
        attach_stacktrace=True,
        release=os.getenv("GIT_SHA", "unknown"),
        server_name=service_name,
        before_send=_before_send_sentry,
    )

    logger.info(
        "Sentry initialized",
        service=service_name,
        environment=ENVIRONMENT,
        traces_sample_rate=traces_sample_rate,
    )


def _before_send_sentry(event, hint):
    """Filter and modify events before sending to Sentry.

    Args:
        event: Sentry event
        hint: Additional information about the event

    Returns:
        Modified event or None to drop the event
    """
    # Don't send events for health check endpoints
    if event.get("request", {}).get("url", "").endswith("/health"):
        return None

    # Add custom tags
    event.setdefault("tags", {})
    event["tags"]["service"] = SERVICE_NAME
    event["tags"]["environment"] = ENVIRONMENT

    return event


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses.

    Adds:
    - Request ID (correlation ID) to all requests
    - Structured logging of request/response details
    - Performance timing
    """

    async def dispatch(self, request: Request, call_next):
        """Process request and log details.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            HTTP response
        """
        # Generate correlation ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Start timer
        start_time = time.time()

        # Log incoming request
        logger.info(
            "Incoming request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        # Process request
        try:
            response = await call_next(request)
        except Exception as exc:
            # Log exception
            logger.error(
                "Request failed with exception",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error=str(exc),
                exc_info=True,
            )
            raise

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log response
        log_func = logger.info if response.status_code < 400 else logger.warning
        if response.status_code >= 500:
            log_func = logger.error

        log_func(
            "Request completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


def add_monitoring(app: FastAPI, service_name: str) -> None:
    """Add comprehensive monitoring to a FastAPI application.

    This includes:
    - Structured logging
    - Sentry error tracking
    - Request/response logging
    - Health check endpoint

    Args:
        app: FastAPI application instance
        service_name: Name of the microservice
    """
    # Setup logging
    setup_logging(service_name)

    # Setup Sentry
    setup_sentry(service_name)

    # Add logging middleware
    app.add_middleware(LoggingMiddleware)

    # Add health check endpoint (if not already present)
    @app.get("/health", tags=["monitoring"])
    async def health_check():
        """Health check endpoint for monitoring and load balancers.

        Returns:
            Health status with service information
        """
        return {
            "status": "healthy",
            "service": service_name,
            "environment": ENVIRONMENT,
            "version": os.getenv("GIT_SHA", "unknown"),
        }

    @app.get("/health/ready", tags=["monitoring"])
    async def readiness_check():
        """Readiness check endpoint (for Kubernetes).

        Returns:
            Readiness status
        """
        # Add custom readiness checks here (database connection, etc.)
        return {
            "status": "ready",
            "service": service_name,
        }

    @app.get("/health/live", tags=["monitoring"])
    async def liveness_check():
        """Liveness check endpoint (for Kubernetes).

        Returns:
            Liveness status
        """
        return {
            "status": "alive",
            "service": service_name,
        }

    logger.info(
        "Monitoring configured",
        service=service_name,
        endpoints=["/health", "/health/ready", "/health/live"],
    )


def log_startup_info(service_name: str, port: int, **kwargs) -> None:
    """Log service startup information.

    Args:
        service_name: Name of the microservice
        port: Port number the service is running on
        **kwargs: Additional information to log
    """
    logger.info(
        f"🚀 {service_name.upper()} service starting",
        service=service_name,
        port=port,
        environment=ENVIRONMENT,
        log_level=LOG_LEVEL,
        sentry_enabled=bool(SENTRY_DSN),
        **kwargs,
    )


def log_shutdown_info(service_name: str) -> None:
    """Log service shutdown information.

    Args:
        service_name: Name of the microservice
    """
    logger.info(
        f"🛑 {service_name.upper()} service shutting down",
        service=service_name,
    )
