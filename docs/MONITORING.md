# Monitoring and Logging Documentation

This document describes the monitoring, logging, and error tracking setup for MS2 QBank.

## Overview

MS2 QBank uses a comprehensive monitoring stack:
- **Loguru** - Structured logging with JSON output
- **Sentry** - Error tracking and performance monitoring
- **Health Checks** - Kubernetes-style health endpoints
- **Request Tracing** - Correlation IDs for distributed tracing

## Architecture

```
┌─────────────┐
│   Request   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│  LoggingMiddleware          │
│  - Generate Request ID      │
│  - Log request/response     │
│  - Measure duration         │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│  FastAPI Endpoint           │
│  - Business logic           │
│  - Structured logging       │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│  Sentry (on errors)         │
│  - Capture exceptions       │
│  - Performance traces       │
└─────────────────────────────┘
```

## Features

### 1. Structured Logging

All logs are structured with consistent fields:

```python
logger.info(
    "User logged in successfully",
    user_id=user.id,
    email=user.email,
)
```

Output:
```
2025-01-15 10:30:45.123 | INFO     | users:login:182 | User logged in successfully
{
    "user_id": 123,
    "email": "student@example.com",
    "service": "users",
    "environment": "production",
    "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### 2. Request/Response Logging

Every HTTP request is automatically logged with:
- Request ID (correlation ID)
- HTTP method and path
- Client IP address
- User agent
- Response status code
- Duration in milliseconds

Example log:
```
2025-01-15 10:30:45 | INFO | Incoming request
{
    "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "method": "POST",
    "path": "/auth/login",
    "client_ip": "192.168.1.100",
    "user_agent": "Mozilla/5.0 ..."
}

2025-01-15 10:30:45.250 | INFO | Request completed
{
    "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "method": "POST",
    "path": "/auth/login",
    "status_code": 200,
    "duration_ms": 250.45
}
```

### 3. Correlation IDs

Each request gets a unique correlation ID that:
- Flows through all log messages
- Is returned in the `X-Request-ID` response header
- Can be used to trace a single request through multiple services

### 4. Sentry Integration

Automatic error tracking with Sentry:
- Captures all uncaught exceptions
- Performance monitoring (10% sample rate)
- Release tracking with Git SHA
- Environment tagging (development, staging, production)
- Filters out health check endpoints

### 5. Health Check Endpoints

Three health check endpoints for different purposes:

#### `/health` - Basic Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{
    "status": "healthy",
    "service": "users",
    "environment": "development",
    "version": "abc123def"
}
```

#### `/health/ready` - Readiness Check
For load balancers and orchestrators. Returns when service is ready to accept traffic.

```bash
curl http://localhost:8000/health/ready
```

#### `/health/live` - Liveness Check
For Kubernetes/Docker. Returns if service is alive (not deadlocked).

```bash
curl http://localhost:8000/health/live
```

## Setup

### 1. Installation

Dependencies are already in `requirements.txt`:
```
loguru>=0.7,<0.8
sentry-sdk[fastapi]>=1.40,<2.0
python-json-logger>=2.0,<3.0
```

Install with:
```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Configure monitoring in `.env`:

```bash
# Environment
ENVIRONMENT=production  # development, staging, or production

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
SERVICE_NAME=users  # Set by docker-compose for each service

# Sentry (optional but recommended for production)
SENTRY_DSN=https://your-key@sentry.io/project-id
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of transactions

# Git SHA for release tracking (set by CI/CD)
GIT_SHA=abc123def456
```

### 3. Service Integration

Add monitoring to any FastAPI app:

```python
from fastapi import FastAPI
from common.logging import add_monitoring, log_startup_info

# Create app
app = FastAPI(title="My Service")

# Add monitoring (logging, Sentry, health checks)
add_monitoring(app, service_name="my_service")

# Use logger
from loguru import logger

@app.post("/endpoint")
def my_endpoint():
    logger.info("Processing request", extra_field="value")
    return {"status": "ok"}
```

### 4. Sentry Setup

1. **Create Sentry Account**
   - Go to https://sentry.io
   - Create a free account
   - Create a new project (select "FastAPI")

2. **Get DSN**
   - Copy your DSN from project settings
   - It looks like: `https://key@sentry.io/project-id`

3. **Add to Environment**
   ```bash
   export SENTRY_DSN="https://your-key@sentry.io/project-id"
   ```

4. **Deploy**
   - Errors will automatically appear in Sentry dashboard
   - Set up alerts for critical errors
   - Review performance traces

## Usage

### Application Logging

Use the logger throughout your code:

```python
from loguru import logger

# Info level (general information)
logger.info("User action completed", user_id=123, action="update_profile")

# Warning level (potential issues)
logger.warning("Rate limit approaching", user_id=123, requests=95, limit=100)

# Error level (errors that were handled)
logger.error("Payment failed", user_id=123, error="Card declined", exc_info=True)

# Debug level (detailed debugging)
logger.debug("Cache lookup", key="user:123", hit=True)
```

### Correlation IDs

Access the request ID in your endpoints:

```python
from fastapi import Request

@app.get("/endpoint")
def my_endpoint(request: Request):
    request_id = request.state.request_id
    logger.info("Processing", request_id=request_id)
    return {"request_id": request_id}
```

### Sentry Context

Add extra context to Sentry reports:

```python
from sentry_sdk import capture_exception, set_tag, set_context

# Add tags
set_tag("user_tier", "premium")
set_tag("feature_flag", "new_ui")

# Add context
set_context("payment", {
    "amount": 99.99,
    "currency": "USD",
    "payment_method": "card"
})

# Capture exception
try:
    process_payment()
except PaymentError as e:
    capture_exception(e)
```

## Log Levels

Use appropriate log levels:

| Level    | When to Use |
|----------|-------------|
| DEBUG    | Detailed debugging information (not in production) |
| INFO     | General information about system operation |
| WARNING  | Potentially harmful situations |
| ERROR    | Error events that might still allow the app to continue |
| CRITICAL | Severe errors that might cause the application to abort |

**Production Recommendation**: Set `LOG_LEVEL=INFO` or `WARNING`

## Log Rotation

Logs are automatically rotated in production:
- **Size**: 500 MB per file
- **Retention**: 10 days
- **Compression**: ZIP compression after rotation
- **Format**: JSON for easy parsing

Logs location: `/app/logs/{service_name}.json`

## Monitoring Best Practices

### 1. Always Include Context

❌ **Bad:**
```python
logger.info("Login failed")
```

✅ **Good:**
```python
logger.info("Login failed", email=email, reason="Invalid password")
```

### 2. Don't Log Sensitive Data

❌ **Bad:**
```python
logger.info("User logged in", password=password, ssn=ssn)
```

✅ **Good:**
```python
logger.info("User logged in", user_id=user.id, email=user.email)
```

### 3. Use Structured Logging

❌ **Bad:**
```python
logger.info(f"User {user_id} paid ${amount}")
```

✅ **Good:**
```python
logger.info("Payment processed", user_id=user_id, amount=amount, currency="USD")
```

### 4. Log Important Events

Always log:
- Authentication events (login, logout, failed attempts)
- Authorization failures
- Payment transactions
- Data mutations (create, update, delete)
- External API calls
- Errors and exceptions

### 5. Use Correlation IDs

When making requests to other services, pass the correlation ID:

```python
import httpx

async def call_external_service(request: Request):
    request_id = request.state.request_id

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.example.com/data",
            headers={"X-Request-ID": request_id}
        )
```

## Troubleshooting

### Logs Not Appearing

1. **Check log level**
   ```bash
   echo $LOG_LEVEL
   ```
   If set to `ERROR`, you won't see `INFO` logs.

2. **Check Sentry DSN**
   ```bash
   echo $SENTRY_DSN
   ```
   Should not be empty in production.

3. **Check Docker volumes**
   ```bash
   docker-compose exec users ls -la /app/logs
   ```

### Sentry Not Receiving Events

1. **Test Sentry connection**
   ```python
   from sentry_sdk import capture_message
   capture_message("Test event from MS2 QBank")
   ```

2. **Check environment**
   - Sentry only sends events in non-development environments
   - Set `ENVIRONMENT=production` or `ENVIRONMENT=staging`

3. **Check sample rate**
   - Performance traces are sampled at 10% by default
   - Errors are always sent (100%)

### High Log Volume

If logs are too verbose:

1. **Increase log level**
   ```bash
   LOG_LEVEL=WARNING  # Only warnings and errors
   ```

2. **Filter noisy endpoints**
   Edit `src/common/logging.py` to filter specific paths

3. **Reduce Sentry sample rate**
   ```bash
   SENTRY_TRACES_SAMPLE_RATE=0.01  # 1% instead of 10%
   ```

## Metrics and Alerts

### Key Metrics to Monitor

1. **Error Rate**
   - Track errors per minute
   - Alert if >10 errors/min

2. **Response Time**
   - P50, P95, P99 latency
   - Alert if P95 >2 seconds

3. **Request Rate**
   - Requests per second
   - Alert on sudden spikes or drops

4. **Health Check Failures**
   - Alert immediately if health checks fail

### Setting Up Alerts

#### Sentry Alerts

1. Go to **Alerts** in Sentry dashboard
2. Create new alert rule:
   - **Error Rate**: >10 errors in 1 minute
   - **New Issue**: Alert on first occurrence
   - **Regression**: Alert when resolved issue returns

#### Docker Health Checks

Health checks are configured in `docker-compose.yml`:

```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

Monitor with:
```bash
docker-compose ps
# Shows health status for each container
```

## Integration with Monitoring Tools

### Grafana + Prometheus

For advanced metrics visualization:

1. **Install Prometheus exporter**
   ```bash
   pip install prometheus-fastapi-instrumentator
   ```

2. **Add to app**
   ```python
   from prometheus_fastapi_instrumentator import Instrumentator

   Instrumentator().instrument(app).expose(app)
   ```

3. **Scrape metrics**
   Prometheus scrapes `/metrics` endpoint

### ELK Stack (Elasticsearch, Logstash, Kibana)

For log aggregation:

1. Logs are already in JSON format
2. Configure Filebeat to ship logs to Logstash
3. Visualize in Kibana

### Datadog

For comprehensive monitoring:

1. Install Datadog agent
2. Configure log collection from `/app/logs/`
3. APM traces are compatible with Sentry format

## Cost Optimization

### Sentry Costs

- **Free tier**: 5,000 events/month
- **Team plan**: $26/month for 50,000 events
- **Business**: Custom pricing

**Tips to reduce costs:**
1. Filter health check endpoints (already done)
2. Reduce trace sample rate
3. Use `before_send` to filter noisy errors

### Log Storage Costs

- Use log rotation (already configured)
- Ship old logs to cheap storage (S3, GCS)
- Set retention policy (10 days by default)

## Next Steps

1. **Set up Sentry** (5 minutes)
   - Create account at https://sentry.io
   - Add DSN to `.env`
   - Deploy and verify errors appear

2. **Configure Alerts** (10 minutes)
   - Set up email alerts in Sentry
   - Configure PagerDuty/Slack integration

3. **Dashboard** (30 minutes)
   - Create Sentry dashboard
   - Pin key metrics
   - Share with team

4. **Runbook** (1 hour)
   - Document common errors
   - Create troubleshooting guide
   - Define on-call procedures

## References

- [Loguru Documentation](https://loguru.readthedocs.io/)
- [Sentry FastAPI Integration](https://docs.sentry.io/platforms/python/guides/fastapi/)
- [Twelve-Factor App: Logs](https://12factor.net/logs)
- [Structured Logging Best Practices](https://www.loggly.com/ultimate-guide/python-logging-basics/)
