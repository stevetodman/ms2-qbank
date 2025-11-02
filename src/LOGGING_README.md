# Structured Logging Guide

## Overview

MS2 QBank uses structured JSON logging for production deployments, enabling:
- Log aggregation (ELK Stack, Splunk, CloudWatch)
- Request tracing via correlation IDs
- Sensitive data masking
- Performance monitoring

## Quick Start

### 1. Configure Logging at Startup

Add to your service's `create_app()` or startup:

```python
from logging_config import configure_logging

# Development (human-readable)
configure_logging(level="DEBUG", service_name="users-api", json_format=False)

# Production (JSON for aggregation)
configure_logging(level="INFO", service_name="users-api", json_format=True)
```

### 2. Add Request Logging Middleware

```python
from fastapi import FastAPI
from logging_config import RequestLoggingMiddleware

app = FastAPI()
app.add_middleware(RequestLoggingMiddleware)
```

### 3. Use Structured Logging

```python
from logging_config import get_logger

logger = get_logger(__name__)

# Simple log
logger.info("User logged in")

# With context (recommended)
logger.info("User logged in", extra={
    "user_id": 123,
    "email": "user@example.com",
    "login_method": "password",
})

# Error logging
try:
    process_payment(user_id)
except Exception:
    logger.error("Payment processing failed", extra={
        "user_id": user_id,
        "amount": 99.99,
    }, exc_info=True)
```

## Log Output Format

### Development (Human-Readable)
```
2025-01-10 14:23:15 - users.auth - INFO - User logged in
2025-01-10 14:23:16 - users.auth - ERROR - Login failed
```

### Production (JSON)
```json
{
  "timestamp": "2025-01-10T14:23:15.123Z",
  "level": "INFO",
  "logger": "users.auth",
  "message": "User logged in",
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": 123,
  "email": "user@example.com"
}
```

## Request Logging

The `RequestLoggingMiddleware` automatically logs:

**Incoming Request:**
```json
{
  "timestamp": "2025-01-10T14:23:15.000Z",
  "level": "INFO",
  "logger": "http.request",
  "message": "Incoming request",
  "correlation_id": "abc123",
  "method": "POST",
  "path": "/api/users/login",
  "query_params": {},
  "headers": {
    "content-type": "application/json",
    "authorization": "***REDACTED***"
  },
  "client_ip": "192.168.1.100"
}
```

**Completed Request:**
```json
{
  "timestamp": "2025-01-10T14:23:15.234Z",
  "level": "INFO",
  "logger": "http.request",
  "message": "Request completed",
  "correlation_id": "abc123",
  "method": "POST",
  "path": "/api/users/login",
  "status_code": 200,
  "duration_ms": 234.56
}
```

## Correlation IDs

Correlation IDs enable request tracing across services:

1. **Client sends header:** `X-Correlation-ID: abc123`
2. **Service logs include:** `"correlation_id": "abc123"`
3. **Response includes header:** `X-Correlation-ID: abc123`

If no correlation ID is provided, one is generated automatically.

### Propagating Across Services

```python
import httpx
from logging_config import correlation_id_var

async def call_other_service():
    correlation_id = correlation_id_var.get()
    headers = {"X-Correlation-ID": correlation_id} if correlation_id else {}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://other-service/api/endpoint",
            headers=headers
        )
```

## Sensitive Data Masking

The following are automatically masked in logs:

- `password`
- `token`
- `secret`
- `api_key`
- `authorization`
- `jwt`
- `refresh_token`
- `access_token`

Example:
```python
logger.info("Token generated", extra={
    "user_id": 123,
    "token": "eyJhbGciOiJIUzI1NiIs...",  # Will be masked
})

# Output:
# "token": "***REDACTED***"
```

## Best Practices

### ✅ DO

```python
# Include relevant context
logger.info("Assessment submitted", extra={
    "user_id": user_id,
    "assessment_id": assessment_id,
    "score": 85.5,
    "duration_seconds": 1234,
})

# Log at appropriate levels
logger.debug("Cache hit", extra={"key": "user:123"})
logger.info("User action completed", extra={"action": "create_deck"})
logger.warning("Rate limit approaching", extra={"user_id": 123, "requests": 95})
logger.error("Database connection failed", exc_info=True)

# Use exc_info for exceptions
try:
    risky_operation()
except Exception:
    logger.error("Operation failed", exc_info=True)
```

### ❌ DON'T

```python
# Don't log sensitive data without masking
logger.info(f"User password: {password}")  # BAD!

# Don't use string formatting (use extra dict)
logger.info(f"User {user_id} logged in")  # Suboptimal

# Don't log huge objects
logger.info("Processing", extra={"data": giant_json_blob})  # BAD!

# Don't spam logs
for item in list_of_10000_items:
    logger.info(f"Processing {item}")  # BAD!
```

## Log Levels

| Level | When to Use | Example |
|-------|-------------|---------|
| DEBUG | Development details, temporary debugging | "Cache key generated: user:123" |
| INFO | Normal operations, user actions | "User logged in", "Assessment completed" |
| WARNING | Recoverable issues, deprecations | "API rate limit approaching", "Using deprecated endpoint" |
| ERROR | Errors requiring attention | "Payment failed", "Database connection lost" |
| CRITICAL | Service-wide failures | "Database unavailable", "Out of memory" |

## Integration with Log Aggregation

### ELK Stack (Elasticsearch, Logstash, Kibana)

1. Configure services to output JSON logs
2. Use Filebeat or Docker logging driver to ship logs
3. Parse JSON in Logstash
4. Visualize in Kibana dashboards

### CloudWatch (AWS)

```python
# Use awslogs driver in docker-compose.yml
logging:
  driver: awslogs
  options:
    awslogs-group: /ms2-qbank/users-api
    awslogs-stream: ${HOSTNAME}
    awslogs-create-group: true
```

### Splunk

Configure HTTP Event Collector (HEC) endpoint:
```python
import logging_config

# Send logs to Splunk via HTTP handler
# (Implementation left as exercise - use splunk-sdk)
```

## Performance Considerations

- JSON serialization adds ~2-5ms overhead per log
- Use appropriate log levels (INFO in production, DEBUG in development)
- Don't log in tight loops
- Truncate large values (automatically done for strings >1000 chars)

## Monitoring Queries

Example queries for common monitoring tasks:

### Error Rate
```
SELECT count(*) FROM logs
WHERE level='ERROR'
AND timestamp > now() - interval '1 hour'
GROUP BY service
```

### Slow Requests
```
SELECT * FROM logs
WHERE logger='http.request'
AND duration_ms > 1000
ORDER BY duration_ms DESC
LIMIT 100
```

### User Activity
```
SELECT user_id, count(*) as actions
FROM logs
WHERE user_id IS NOT NULL
AND timestamp > now() - interval '1 day'
GROUP BY user_id
ORDER BY actions DESC
```

## Environment Configuration

```bash
# .env file
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json  # json or text
SERVICE_NAME=users-api
```

```python
import os
from logging_config import configure_logging

configure_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    service_name=os.getenv("SERVICE_NAME", "ms2-qbank"),
    json_format=(os.getenv("LOG_FORMAT", "json") == "json"),
)
```

## Migration from Print Statements

```python
# Before (bad)
print(f"User {user_id} logged in")
print(f"Error: {str(e)}")

# After (good)
logger = get_logger(__name__)
logger.info("User logged in", extra={"user_id": user_id})
logger.error("Operation failed", exc_info=True)
```

## Testing with Structured Logs

```python
import logging
from logging_config import configure_logging, StructuredFormatter

def test_user_login(caplog):
    configure_logging(level="DEBUG", json_format=False)

    with caplog.at_level(logging.INFO):
        # Your test code here
        user.login()

    # Assert log messages
    assert "User logged in" in caplog.text
    assert any(record.user_id == 123 for record in caplog.records)
```

## References

- Python Logging: https://docs.python.org/3/library/logging.html
- Structured Logging Best Practices: https://www.structlog.org/
- ELK Stack: https://www.elastic.co/elastic-stack
- OpenTelemetry Logs: https://opentelemetry.io/docs/concepts/observability-primer/#logs
