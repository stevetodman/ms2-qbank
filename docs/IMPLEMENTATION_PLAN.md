# MS2 QBank Platform: Implementation Plan & Roadmap

**Document Version:** 1.0
**Created:** November 1, 2025
**Status:** Active
**Based on:** TECHNICAL_EVALUATION.md

---

## Executive Summary

This document provides an actionable implementation plan for taking MS2 QBank from its current state (feature-complete reference implementation) to a production-ready, scalable medical education platform. The plan is organized into three phases spanning 3-6 months.

**Current Status:** ★★★★☆ (4.5/5) - Excellent code quality, needs infrastructure
**Target Status:** ★★★★★ (5/5) - Production-deployed with 1,000+ concurrent users
**Estimated Effort:** 320 hours (2 developers × 2 months)

---

## Table of Contents

1. [Phase 1: Critical Path to Production (1-2 weeks)](#phase-1-critical-path-to-production)
2. [Phase 2: Infrastructure & Operational Excellence (1 month)](#phase-2-infrastructure--operational-excellence)
3. [Phase 3: Scale & Enhancement (2-3 months)](#phase-3-scale--enhancement)
4. [Task Breakdown & Assignments](#task-breakdown--assignments)
5. [Risk Assessment](#risk-assessment)
6. [Success Metrics](#success-metrics)

---

## Phase 1: Critical Path to Production

**Duration:** 1-2 weeks (80 hours)
**Goal:** Deploy first production version supporting 100-500 concurrent users
**Priority:** CRITICAL

### 1.1 Database Migration to PostgreSQL

**Priority:** P0 (Blocker)
**Effort:** 4-6 hours
**Owner:** Backend Engineer
**Dependencies:** None

**Current Issue:**
- SQLite cannot handle concurrent writes from multiple users
- Limited to ~100 concurrent users
- No replication or high availability

**Task Breakdown:**
```bash
# 1. Install PostgreSQL locally (30 min)
brew install postgresql@15  # macOS
# OR
sudo apt-get install postgresql-15  # Linux

# 2. Create databases (15 min)
createdb ms2qbank_users
createdb ms2qbank_flashcards
createdb ms2qbank_analytics
createdb ms2qbank_videos
createdb ms2qbank_library
createdb ms2qbank_assessments
createdb ms2qbank_planner
createdb ms2qbank_reviews

# 3. Update connection strings (1 hour)
# src/users/store.py
DATABASE_URL = "postgresql://user:password@localhost:5432/ms2qbank_users"

# Repeat for all 8 services
# Test each service individually

# 4. Run migrations (30 min)
# SQLModel auto-creates tables, but verify schema
python -m src.users.app  # Should create tables automatically

# 5. Test all services (2 hours)
pytest tests/test_*.py  # Run full test suite
```

**Verification:**
- [ ] All 8 services connect to PostgreSQL
- [ ] All tests pass
- [ ] Data persists across service restarts
- [ ] Concurrent writes work (test with 10 simultaneous requests)

**Rollback Plan:** Keep SQLite files as backup, connection strings in environment variables

---

### 1.2 Add JWT Refresh Tokens

**Priority:** P0 (Critical for UX)
**Effort:** 6-8 hours
**Owner:** Backend Engineer
**Dependencies:** None

**Current Issue:**
- Users must re-login every 7 days
- No way to revoke compromised tokens
- Poor user experience for long-term users

**Implementation:**

**Step 1: Update Token Models** (1 hour)
```python
# src/users/models.py
class RefreshTokenDB(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    user_id: int = SQLField(foreign_key="users.id", index=True)
    token: str = SQLField(unique=True, index=True)
    expires_at: datetime
    created_at: datetime = SQLField(default_factory=lambda: datetime.now(timezone.utc))
    revoked: bool = SQLField(default=False)
    device_info: Optional[str] = None  # User agent for tracking
```

**Step 2: Update Auth Module** (2 hours)
```python
# src/users/auth.py
def create_token_pair(user_id: int, email: str) -> dict:
    """Generate access + refresh token pair."""
    # Access token: 15 minutes
    access_token = jwt.encode({
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(minutes=15),
        "type": "access"
    }, SECRET_KEY, algorithm="HS256")

    # Refresh token: 7 days
    refresh_token = jwt.encode({
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=7),
        "type": "refresh"
    }, SECRET_KEY, algorithm="HS256")

    # Store refresh token in database
    store_refresh_token(user_id, refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": 900  # 15 minutes in seconds
    }

def refresh_access_token(refresh_token: str) -> dict:
    """Generate new access token from valid refresh token."""
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=["HS256"])

        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(401, "Invalid token type")

        # Verify token not revoked
        if is_token_revoked(refresh_token):
            raise HTTPException(401, "Token has been revoked")

        user_id = payload["user_id"]
        user = get_user_by_id(user_id)

        # Generate new access token
        access_token = jwt.encode({
            "user_id": user_id,
            "email": user.email,
            "exp": datetime.utcnow() + timedelta(minutes=15),
            "type": "access"
        }, SECRET_KEY, algorithm="HS256")

        return {
            "access_token": access_token,
            "expires_in": 900
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Refresh token expired - please login again")
```

**Step 3: Add API Endpoint** (1 hour)
```python
# src/users/app.py
@app.post("/auth/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    return refresh_access_token(payload.refresh_token)

@app.post("/auth/logout")
def logout(user_id: int = Depends(get_current_user_id),
           refresh_token: str = Body(...)):
    """Logout and revoke refresh token."""
    revoke_refresh_token(refresh_token)
    return {"message": "Logged out successfully"}
```

**Step 4: Update Frontend** (2 hours)
```typescript
// web/src/context/AuthContext.tsx
const refreshToken = async () => {
  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) throw new Error('No refresh token');

  const response = await fetch('http://localhost:8000/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken })
  });

  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
  return data.access_token;
};

// Add axios interceptor for automatic token refresh
axios.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      try {
        await refreshToken();
        // Retry original request
        return axios(error.config);
      } catch {
        // Refresh failed, logout user
        logout();
      }
    }
    return Promise.reject(error);
  }
);
```

**Step 5: Testing** (2 hours)
```python
# tests/test_refresh_tokens.py
def test_refresh_token_flow():
    # Login and get tokens
    response = client.post("/login", json={"email": "test@example.com", "password": "password"})
    tokens = response.json()

    # Wait for access token to expire (or mock time)
    time.sleep(16 * 60)  # 16 minutes

    # Try to access protected endpoint - should fail
    response = client.get("/profile", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 401

    # Refresh token
    response = client.post("/auth/refresh", json={"refresh_token": tokens['refresh_token']})
    new_token = response.json()["access_token"]

    # Try again with new token - should succeed
    response = client.get("/profile", headers={"Authorization": f"Bearer {new_token}"})
    assert response.status_code == 200

def test_revoked_token_fails():
    # Get tokens
    tokens = login()

    # Logout (revokes refresh token)
    client.post("/auth/logout", json={"refresh_token": tokens['refresh_token']})

    # Try to refresh with revoked token - should fail
    response = client.post("/auth/refresh", json={"refresh_token": tokens['refresh_token']})
    assert response.status_code == 401
```

**Verification:**
- [ ] Users stay logged in without manual re-login
- [ ] Access token expires after 15 minutes
- [ ] Refresh token works to get new access token
- [ ] Logout revokes refresh token
- [ ] Old refresh tokens can't be reused

---

### 1.3 Containerize Services with Docker

**Priority:** P0 (Required for deployment)
**Effort:** 8-10 hours
**Owner:** DevOps/Backend Engineer
**Dependencies:** 1.1 (PostgreSQL migration)

**Task Breakdown:**

**Step 1: Create Individual Dockerfiles** (3 hours)
```dockerfile
# src/users/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY src/users ./src/users

# Expose port
EXPOSE 8000

# Run service
CMD ["uvicorn", "src.users.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

Repeat for all 9 services (change port numbers: 8000-8008)

**Step 2: Create Docker Compose** (3 hours)
```yaml
# docker-compose.yml
version: '3.8'

services:
  # Database
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD:-secret}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-databases.sh:/docker-entrypoint-initdb.d/init-databases.sh
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis for caching (future)
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s

  # Users Service
  users:
    build:
      context: .
      dockerfile: src/users/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD:-secret}@postgres:5432/ms2qbank_users
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

  # Flashcards Service
  flashcards:
    build:
      context: .
      dockerfile: src/flashcards/Dockerfile
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD:-secret}@postgres:5432/ms2qbank_flashcards
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

  # ... Repeat for services on ports 8002-8008

  # Frontend (Nginx serving built React app)
  frontend:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./web/dist:/usr/share/nginx/html
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl  # SSL certificates
    depends_on:
      - users
      - flashcards
      - assessments
      - videos
      - library
      - planner
      - questions
      - reviews
      - analytics
    restart: unless-stopped

volumes:
  postgres_data:
```

**Step 3: Create Init Script** (1 hour)
```bash
# scripts/init-databases.sh
#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "postgres" <<-EOSQL
    CREATE DATABASE ms2qbank_users;
    CREATE DATABASE ms2qbank_flashcards;
    CREATE DATABASE ms2qbank_analytics;
    CREATE DATABASE ms2qbank_videos;
    CREATE DATABASE ms2qbank_library;
    CREATE DATABASE ms2qbank_assessments;
    CREATE DATABASE ms2qbank_planner;
    CREATE DATABASE ms2qbank_reviews;
EOSQL
```

**Step 4: Create Nginx Config** (2 hours)
```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream users_backend {
        server users:8000;
    }

    upstream flashcards_backend {
        server flashcards:8001;
    }

    # ... repeat for all services

    server {
        listen 80;
        server_name localhost;

        # Frontend
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
        }

        # API Proxy
        location /api/users {
            proxy_pass http://users_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /api/flashcards {
            proxy_pass http://flashcards_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # ... repeat for all services
    }
}
```

**Step 5: Testing** (1 hour)
```bash
# Build and start all services
docker-compose build
docker-compose up -d

# Verify all services are running
docker-compose ps

# Test health endpoints
curl http://localhost:8000/health  # Users service
curl http://localhost:8001/health  # Flashcards service
# ... test all services

# Test frontend
curl http://localhost/

# Check logs
docker-compose logs -f users
docker-compose logs -f postgres

# Run tests in containers
docker-compose exec users pytest tests/

# Cleanup
docker-compose down
```

**Verification:**
- [ ] All services build successfully
- [ ] All services start and stay running
- [ ] Services can connect to PostgreSQL
- [ ] Frontend loads and can call APIs
- [ ] Tests pass in containerized environment

---

### 1.4 Optimize Analytics Percentile Calculation

**Priority:** P1 (Important for scale)
**Effort:** 4-6 hours
**Owner:** Backend Engineer
**Dependencies:** 1.1 (PostgreSQL migration)

**Current Issue:**
- O(n²) algorithm: loops through all users
- 10,000 users = 10,000 database queries
- Would timeout with large user base

**Solution: Single SQL Query with Aggregation**

**Step 1: Create Aggregated View** (2 hours)
```python
# src/analytics/user_store.py
def compute_percentile_ranking_optimized(self, user_id: int) -> PercentileRanking:
    """Compute user's percentile using single SQL aggregation query."""
    with Session(self.engine) as session:
        # Single query to get all users' aggregated stats
        query = """
        WITH user_stats AS (
            SELECT
                user_id,
                COUNT(*) as attempt_count,
                AVG(CASE WHEN is_correct THEN 1.0 ELSE 0.0 END) as accuracy,
                AVG(CASE WHEN time_seconds IS NOT NULL THEN time_seconds END) as avg_time
            FROM question_attempts
            GROUP BY user_id
        ),
        current_user AS (
            SELECT * FROM user_stats WHERE user_id = :user_id
        )
        SELECT
            (SELECT COUNT(*) FROM user_stats) as total_users,
            (SELECT COUNT(*) FROM user_stats
             WHERE accuracy < (SELECT accuracy FROM current_user)) as better_accuracy_count,
            (SELECT COUNT(*) FROM user_stats
             WHERE avg_time > (SELECT avg_time FROM current_user)) as better_speed_count,
            (SELECT COUNT(*) FROM user_stats
             WHERE attempt_count < (SELECT attempt_count FROM current_user)) as better_volume_count,
            (SELECT accuracy FROM current_user) as user_accuracy,
            (SELECT avg_time FROM current_user) as user_avg_time,
            (SELECT attempt_count FROM current_user) as user_volume
        """

        result = session.execute(query, {"user_id": user_id}).fetchone()

        if not result or result.total_users == 0:
            return PercentileRanking(
                user_id=user_id,
                overall_percentile=0.0,
                accuracy_percentile=0.0,
                speed_percentile=0.0,
                volume_percentile=0.0,
                total_users=0
            )

        # Calculate percentiles from counts
        total = result.total_users - 1  # Exclude self
        accuracy_pct = (result.better_accuracy_count / total * 100) if total > 0 else 0
        speed_pct = (result.better_speed_count / total * 100) if total > 0 else 0
        volume_pct = (result.better_volume_count / total * 100) if total > 0 else 0

        # Weighted average
        overall_pct = (
            accuracy_pct * 0.5 +
            speed_pct * 0.25 +
            volume_pct * 0.25
        )

        return PercentileRanking(
            user_id=user_id,
            overall_percentile=round(overall_pct, 2),
            accuracy_percentile=round(accuracy_pct, 2),
            speed_percentile=round(speed_pct, 2),
            volume_percentile=round(volume_pct, 2),
            total_users=result.total_users
        )
```

**Step 2: Add Caching** (1 hour)
```python
from functools import lru_cache
from datetime import datetime, timedelta

# In-memory cache with TTL
percentile_cache = {}
CACHE_TTL = 3600  # 1 hour

def get_percentile_ranking_cached(self, user_id: int) -> PercentileRanking:
    """Get percentile with 1-hour cache."""
    cache_key = f"percentile:{user_id}"

    # Check cache
    if cache_key in percentile_cache:
        cached_value, cached_time = percentile_cache[cache_key]
        if datetime.now() - cached_time < timedelta(seconds=CACHE_TTL):
            return cached_value

    # Compute fresh value
    result = self.compute_percentile_ranking_optimized(user_id)

    # Store in cache
    percentile_cache[cache_key] = (result, datetime.now())

    return result

def invalidate_percentile_cache(self, user_id: int):
    """Invalidate cache when user completes questions."""
    cache_key = f"percentile:{user_id}"
    if cache_key in percentile_cache:
        del percentile_cache[cache_key]
```

**Step 3: Update API to Use Optimized Version** (1 hour)
```python
# src/analytics/user_app.py
@app.get("/analytics/percentile", response_model=PercentileRanking)
def get_user_percentile(
    user_id: int = Depends(get_current_user_id),
    store: UserAnalyticsStore = Depends(get_store)
):
    """Get user's percentile ranking (cached)."""
    return store.get_percentile_ranking_cached(user_id)
```

**Step 4: Testing** (2 hours)
```python
# tests/test_analytics_performance.py
import time

def test_percentile_performance():
    """Test that percentile calculation is fast even with many users."""
    # Create 1000 test users with attempts
    for i in range(1000):
        user_id = i + 1
        for j in range(10):  # 10 attempts each
            store.record_attempt(
                user_id=user_id,
                question_id=f"q{j}",
                correct_answer="A",
                is_correct=(j % 2 == 0),
                subject="Anatomy"
            )

    # Time the percentile calculation
    start = time.time()
    result = store.compute_percentile_ranking_optimized(500)
    duration = time.time() - start

    # Should complete in < 0.1 seconds even with 1000 users
    assert duration < 0.1
    assert result.total_users == 1000

def test_percentile_cache():
    """Test that caching works."""
    user_id = 1

    # First call - cache miss
    start = time.time()
    result1 = store.get_percentile_ranking_cached(user_id)
    duration1 = time.time() - start

    # Second call - cache hit
    start = time.time()
    result2 = store.get_percentile_ranking_cached(user_id)
    duration2 = time.time() - start

    # Cache hit should be much faster
    assert duration2 < duration1 / 10
    assert result1.overall_percentile == result2.overall_percentile
```

**Verification:**
- [ ] Percentile calculation completes in < 100ms for 1,000 users
- [ ] Percentile calculation completes in < 500ms for 10,000 users
- [ ] Cache reduces response time by 90%+
- [ ] Results are mathematically identical to old implementation

---

## Phase 2: Infrastructure & Operational Excellence

**Duration:** 1 month (120 hours)
**Goal:** Production-grade infrastructure with monitoring, CI/CD, and security
**Priority:** HIGH

### 2.1 CI/CD Pipeline with GitHub Actions

**Priority:** P1
**Effort:** 10-12 hours
**Owner:** DevOps Engineer

**Tasks:**
1. **Create Test Workflow** (3 hours)
   ```yaml
   # .github/workflows/test.yml
   name: Test Suite

   on: [push, pull_request]

   jobs:
     backend-tests:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - uses: actions/setup-python@v4
           with:
             python-version: '3.11'
         - name: Install dependencies
           run: pip install -r requirements.txt
         - name: Run pytest
           run: pytest tests/ --cov=src --cov-report=xml
         - name: Upload coverage
           uses: codecov/codecov-action@v3

     frontend-tests:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - uses: actions/setup-node@v3
           with:
             node-version: '18'
         - name: Install dependencies
           run: cd web && npm install
         - name: Run tests
           run: cd web && npm test
         - name: Build
           run: cd web && npm run build
   ```

2. **Create Build & Deploy Workflow** (4 hours)
   ```yaml
   # .github/workflows/deploy.yml
   name: Build and Deploy

   on:
     push:
       branches: [main]

   jobs:
     build:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3

         - name: Build Docker images
           run: |
             docker-compose build

         - name: Push to Registry
           run: |
             echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
             docker-compose push

     deploy:
       needs: build
       runs-on: ubuntu-latest
       steps:
         - name: Deploy to production
           uses: appleboy/ssh-action@master
           with:
             host: ${{ secrets.PRODUCTION_HOST }}
             username: ${{ secrets.SSH_USER }}
             key: ${{ secrets.SSH_PRIVATE_KEY }}
             script: |
               cd /opt/ms2qbank
               git pull
               docker-compose pull
               docker-compose up -d
               docker-compose exec users alembic upgrade head
   ```

3. **Add Code Quality Checks** (2 hours)
   - Black code formatting
   - Ruff linting
   - mypy type checking
   - ESLint for frontend

4. **Setup Branch Protection** (1 hour)
   - Require PR reviews
   - Require passing tests
   - Require up-to-date branches

5. **Create Deployment Environments** (2 hours)
   - Staging environment
   - Production environment
   - Environment-specific secrets

**Verification:**
- [ ] All tests run on every PR
- [ ] Failed tests block merge
- [ ] Main branch deploys to staging automatically
- [ ] Tagged releases deploy to production
- [ ] Deployment notifications to Slack/Discord

---

### 2.2 Monitoring & Observability Stack

**Priority:** P1
**Effort:** 12-15 hours
**Owner:** DevOps Engineer

**Components:**
1. **Prometheus** (metrics collection)
2. **Grafana** (dashboards)
3. **Loki** (log aggregation)
4. **Sentry** (error tracking)

**Implementation:**

**Step 1: Add Prometheus Instrumentation** (4 hours)
```python
# requirements.txt
prometheus-client==0.18.0
prometheus-fastapi-instrumentator==6.1.0

# src/users/app.py
from prometheus_client import Counter, Histogram, Gauge
from prometheus_fastapi_instrumentator import Instrumentator

# Metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
active_users = Gauge('active_users_total', 'Number of active users')
database_connections = Gauge('database_connections_active', 'Active database connections')

# Instrument app
Instrumentator().instrument(app).expose(app)

# Custom business metrics
@app.post("/login")
def login(...):
    request_count.labels(method='POST', endpoint='/login', status='200').inc()
    with request_duration.time():
        # ... login logic
    active_users.inc()
```

**Step 2: Add Prometheus to Docker Compose** (2 hours)
```yaml
# docker-compose.yml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'

volumes:
  prometheus_data:
```

```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'users_service'
    static_configs:
      - targets: ['users:8000']

  - job_name: 'flashcards_service'
    static_configs:
      - targets: ['flashcards:8001']

  # ... repeat for all services

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
```

**Step 3: Setup Grafana Dashboards** (3 hours)
```yaml
# docker-compose.yml
services:
  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    depends_on:
      - prometheus

volumes:
  grafana_data:
```

Create dashboards:
- **Service Health**: Request rate, error rate, latency (RED metrics)
- **Database Performance**: Query time, connection pool, slow queries
- **Business Metrics**: Daily active users, questions answered, accuracy trends
- **Infrastructure**: CPU, memory, disk usage per service

**Step 4: Setup Sentry for Error Tracking** (2 hours)
```python
# requirements.txt
sentry-sdk[fastapi]==1.38.0

# src/users/app.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="https://your-sentry-dsn@sentry.io/project",
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,  # 10% of transactions
    profiles_sample_rate=0.1,
    environment="production"
)
```

**Step 5: Setup Log Aggregation with Loki** (2 hours)
```yaml
# docker-compose.yml
services:
  loki:
    image: grafana/loki:latest
    volumes:
      - ./loki/loki-config.yml:/etc/loki/local-config.yml
    ports:
      - "3100:3100"

  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log:/var/log
      - ./loki/promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml
```

**Step 6: Alert Rules** (2 hours)
```yaml
# prometheus/alerts.yml
groups:
  - name: service_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate on {{ $labels.service }}"

      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow response time on {{ $labels.service }}"

      - alert: DatabaseConnectionPoolExhausted
        expr: database_connections_active / database_connections_max > 0.9
        for: 5m
        labels:
          severity: critical
```

**Verification:**
- [ ] All services expose /metrics endpoint
- [ ] Prometheus scrapes metrics from all services
- [ ] Grafana dashboards show real-time data
- [ ] Sentry captures errors
- [ ] Alerts fire when thresholds breached
- [ ] Logs aggregated in Loki

---

### 2.3 Security Hardening

**Priority:** P1
**Effort:** 10-12 hours
**Owner:** Security Engineer

**Tasks:**

**1. Rate Limiting** (3 hours)
```python
# requirements.txt
slowapi==0.1.9

# src/users/app.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/login")
@limiter.limit("5/minute")  # Max 5 login attempts per minute
def login(request: Request, ...):
    ...

@app.post("/signup")
@limiter.limit("3/hour")  # Max 3 signups per hour per IP
def signup(request: Request, ...):
    ...

@app.get("/questions/{id}")
@limiter.limit("100/minute")  # Max 100 questions per minute
def get_question(request: Request, ...):
    ...
```

**2. Input Validation & Sanitization** (2 hours)
```python
# src/users/models.py
from pydantic import BaseModel, Field, validator, EmailStr
import bleach

class SignupRequest(BaseModel):
    email: EmailStr  # Validates email format
    password: str = Field(min_length=8, max_length=100)
    name: str = Field(min_length=1, max_length=100)

    @validator('password')
    def validate_password_strength(cls, v):
        """Require strong password."""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v

    @validator('name')
    def sanitize_name(cls, v):
        """Strip HTML tags from name."""
        return bleach.clean(v, strip=True)
```

**3. CORS Configuration** (1 hour)
```python
# src/users/app.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ms2qbank.com",
        "https://www.ms2qbank.com"
    ],  # Don't use * in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
    max_age=3600,  # Cache preflight for 1 hour
)
```

**4. SQL Injection Prevention** (2 hours)
```python
# Already using SQLModel/SQLAlchemy which prevents SQL injection
# But verify all queries use parameterized queries

# ❌ BAD - Vulnerable to SQL injection
query = f"SELECT * FROM users WHERE email = '{email}'"

# ✅ GOOD - Parameterized query
query = select(User).where(User.email == email)

# Audit all raw SQL queries
grep -r "execute(" src/
# Ensure all use parameterized queries
```

**5. Security Headers** (2 hours)
```python
# src/users/app.py
from fastapi.middleware import Middleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["ms2qbank.com", "*.ms2qbank.com"])

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

**6. Dependency Scanning** (2 hours)
```yaml
# .github/workflows/security.yml
name: Security Scan

on: [push, pull_request]

jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Scan Python dependencies
        run: |
          pip install safety
          safety check -r requirements.txt

      - name: Scan Node dependencies
        run: |
          cd web
          npm audit

      - name: SAST scan
        uses: returntocorp/semgrep-action@v1
```

**Verification:**
- [ ] Rate limits block excessive requests
- [ ] All user inputs validated
- [ ] No SQL injection vulnerabilities
- [ ] Security headers present in responses
- [ ] Dependency scan passes
- [ ] CORS restricts to production domains

---

## Phase 3: Scale & Enhancement

**Duration:** 2-3 months (120 hours)
**Goal:** Support 10,000+ users, mobile apps, advanced features
**Priority:** MEDIUM

### 3.1 Redis Caching Layer

**Priority:** P2
**Effort:** 8-10 hours
**Owner:** Backend Engineer

**Use Cases:**
1. **Session storage** - Store JWT refresh tokens
2. **API response caching** - Cache frequently accessed data
3. **Rate limiting** - Distributed rate limiting across multiple instances

**Implementation:**

```python
# requirements.txt
redis==5.0.1

# src/common/redis_client.py
import redis
import json
from typing import Any, Optional

class RedisCache:
    def __init__(self, url: str = "redis://localhost:6379"):
        self.client = redis.from_url(url, decode_responses=True)

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        value = self.client.get(key)
        return json.loads(value) if value else None

    def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL (default 5 minutes)."""
        self.client.setex(key, ttl, json.dumps(value))

    def delete(self, key: str):
        """Delete key from cache."""
        self.client.delete(key)

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        return bool(self.client.exists(key))

# Usage in services
cache = RedisCache()

@app.get("/decks")
def list_decks(...):
    cache_key = f"decks:user:{user_id}:type:{deck_type}"

    # Try cache first
    cached = cache.get(cache_key)
    if cached:
        return cached

    # Query database
    decks = store.list_decks(user_id=user_id, deck_type=deck_type)

    # Cache for 5 minutes
    cache.set(cache_key, decks, ttl=300)

    return decks
```

**Cache Strategy:**
- **User decks list**: 5 min TTL
- **Video metadata**: 1 hour TTL
- **Question bank**: 30 min TTL (questions rarely change)
- **User analytics**: 10 min TTL
- **Percentile rankings**: 1 hour TTL

**Verification:**
- [ ] Cache reduces database queries by 50%+
- [ ] API response time improves by 30%+
- [ ] Cache invalidation works correctly

---

### 3.2 Database Read Replicas

**Priority:** P2
**Effort:** 12-15 hours
**Owner:** Database Administrator

**Goal:** Distribute read queries across multiple database instances

**Implementation:**

```yaml
# docker-compose.yml
services:
  postgres-primary:
    image: postgres:15-alpine
    environment:
      - POSTGRES_PASSWORD=secret
      - POSTGRES_REPLICATION_MODE=master
      - POSTGRES_REPLICATION_USER=replicator
      - POSTGRES_REPLICATION_PASSWORD=replicator_password
    volumes:
      - postgres_primary:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  postgres-replica-1:
    image: postgres:15-alpine
    environment:
      - POSTGRES_MASTER_HOST=postgres-primary
      - POSTGRES_PASSWORD=secret
      - POSTGRES_REPLICATION_MODE=slave
      - POSTGRES_REPLICATION_USER=replicator
      - POSTGRES_REPLICATION_PASSWORD=replicator_password
    ports:
      - "5433:5432"
    depends_on:
      - postgres-primary

  postgres-replica-2:
    image: postgres:15-alpine
    environment:
      - POSTGRES_MASTER_HOST=postgres-primary
      - POSTGRES_PASSWORD=secret
      - POSTGRES_REPLICATION_MODE=slave
      - POSTGRES_REPLICATION_USER=replicator
      - POSTGRES_REPLICATION_PASSWORD=replicator_password
    ports:
      - "5434:5432"
    depends_on:
      - postgres-primary
```

```python
# src/users/store.py
class UserStore:
    def __init__(self):
        # Write to primary
        self.write_engine = create_engine("postgresql://user:pass@postgres-primary:5432/users")

        # Read from replicas (round-robin)
        self.read_engines = [
            create_engine("postgresql://user:pass@postgres-replica-1:5432/users"),
            create_engine("postgresql://user:pass@postgres-replica-2:5432/users"),
        ]
        self.read_index = 0

    def get_read_engine(self):
        """Get next replica in round-robin."""
        engine = self.read_engines[self.read_index]
        self.read_index = (self.read_index + 1) % len(self.read_engines)
        return engine

    def create_user(self, ...):
        """Write to primary."""
        with Session(self.write_engine) as session:
            ...

    def get_user(self, user_id: int):
        """Read from replica."""
        with Session(self.get_read_engine()) as session:
            ...
```

**Verification:**
- [ ] Reads distributed across replicas
- [ ] Writes go to primary only
- [ ] Replication lag < 1 second
- [ ] Failover works if replica goes down

---

### 3.3 Mobile App Development

**Priority:** P2
**Effort:** 200+ hours (separate project)
**Owner:** Mobile Development Team

**Recommendation: React Native**
- Share business logic with web app
- Write once, deploy to iOS and Android
- 70%+ code reuse

**High-level Plan:**
1. Setup React Native project (10 hours)
2. Implement authentication (20 hours)
3. Port QBank practice UI (40 hours)
4. Port flashcard UI (30 hours)
5. Port video player (30 hours)
6. Implement offline mode (40 hours)
7. Add push notifications (15 hours)
8. Testing on devices (20 hours)
9. App store submission (15 hours)

---

## Task Breakdown & Assignments

### Week 1-2: Critical Path (80 hours)

| Task | Owner | Hours | Dependencies |
|------|-------|-------|--------------|
| PostgreSQL Migration | Backend Eng | 6 | None |
| JWT Refresh Tokens | Backend Eng | 8 | None |
| Docker Containers | DevOps | 10 | PostgreSQL |
| Optimize Analytics | Backend Eng | 6 | PostgreSQL |
| Test All Changes | QA | 8 | All above |
| Deploy to Staging | DevOps | 4 | All above |

**Total:** 42 hours (can be parallelized across 2 engineers)

### Week 3-6: Infrastructure (120 hours)

| Task | Owner | Hours | Dependencies |
|------|-------|-------|--------------|
| CI/CD Pipeline | DevOps | 12 | Docker |
| Monitoring Stack | DevOps | 15 | Docker |
| Security Hardening | Security Eng | 12 | None |
| Load Testing | QA | 10 | Monitoring |
| Documentation | Tech Writer | 8 | All |
| Production Deployment | DevOps | 8 | All above |

**Total:** 65 hours

### Month 2-3: Scale & Enhancement (120 hours)

| Task | Owner | Hours | Dependencies |
|------|-------|-------|--------------|
| Redis Caching | Backend Eng | 10 | Production |
| Database Replicas | DBA | 15 | Production |
| CDN Setup | DevOps | 8 | Production |
| Advanced Analytics | Backend Eng | 20 | Redis |
| Mobile App (Phase 1) | Mobile Team | 80 | API stable |
| Performance Tuning | All | 20 | Monitoring data |

---

## Risk Assessment

### High Risk

**1. PostgreSQL Migration Issues**
- **Risk:** Data loss or corruption during migration
- **Mitigation:**
  - Test migration on staging first
  - Keep SQLite backups for 30 days
  - Implement rollback script
  - Monitor closely for first week

**2. Docker Container Performance**
- **Risk:** Services run slower in containers
- **Mitigation:**
  - Benchmark before/after
  - Tune resource limits
  - Use multi-stage builds to reduce image size

### Medium Risk

**3. Downtime During Deployment**
- **Risk:** Users experience service interruption
- **Mitigation:**
  - Blue-green deployment strategy
  - Health checks before switching traffic
  - Rollback plan ready

**4. Database Connection Pool Exhaustion**
- **Risk:** Too many connections with horizontal scaling
- **Mitigation:**
  - Configure pgBouncer connection pooler
  - Monitor connection metrics
  - Set appropriate pool sizes

### Low Risk

**5. Cache Inconsistency**
- **Risk:** Stale data shown to users
- **Mitigation:**
  - Short TTLs (5-10 min max)
  - Cache invalidation on writes
  - Document cache strategy

---

## Success Metrics

### Technical Metrics

**Performance:**
- API response time (P95) < 200ms
- Database query time (P95) < 50ms
- Page load time < 2 seconds
- Time to first byte < 100ms

**Reliability:**
- Uptime > 99.9% (less than 43 minutes downtime per month)
- Error rate < 0.1%
- Mean time to recovery (MTTR) < 15 minutes

**Scalability:**
- Support 1,000+ concurrent users
- Handle 10,000 requests per minute
- Database can scale to 1M+ questions answered per day

### Business Metrics

**Engagement:**
- Daily active users (DAU)
- Questions answered per user per day
- Average session duration
- Retention rate (Day 1, Day 7, Day 30)

**Quality:**
- User-reported bugs < 1 per week
- Customer satisfaction score > 4.5/5
- Net Promoter Score (NPS) > 50

---

## Timeline Summary

**Phase 1: Weeks 1-2** (Critical Path)
- ✅ PostgreSQL migration
- ✅ Refresh tokens
- ✅ Docker containers
- ✅ Analytics optimization
- **Milestone:** Staging deployment complete

**Phase 2: Weeks 3-6** (Infrastructure)
- ✅ CI/CD pipeline
- ✅ Monitoring & alerts
- ✅ Security hardening
- **Milestone:** Production deployment with 100+ users

**Phase 3: Months 2-3** (Scale & Enhancement)
- ✅ Redis caching
- ✅ Database replicas
- ✅ Advanced features
- **Milestone:** Supporting 1,000+ concurrent users

---

## Next Steps

1. **Immediate (Today):**
   - Review and approve this plan
   - Assign task owners
   - Setup development environments
   - Create project tracking board (Jira/Linear)

2. **This Week:**
   - Kickoff meeting with team
   - Start Phase 1 tasks in parallel
   - Setup staging server
   - Order PostgreSQL hosting (if not self-hosted)

3. **First Month:**
   - Complete Phase 1 & 2
   - Deploy to production
   - Monitor closely
   - Gather user feedback

---

## Appendix: Useful Commands

```bash
# Start all services locally
docker-compose up -d

# View logs
docker-compose logs -f [service_name]

# Run tests
docker-compose exec users pytest tests/

# Database backup
docker-compose exec postgres pg_dump -U postgres ms2qbank_users > backup.sql

# Database restore
docker-compose exec -T postgres psql -U postgres ms2qbank_users < backup.sql

# Scale service
docker-compose up -d --scale users=3

# Update service
docker-compose up -d --no-deps --build users

# Production deploy
git pull && docker-compose pull && docker-compose up -d
```

---

**Document Status:** ✅ Ready for Implementation
**Last Updated:** November 1, 2025
**Next Review:** After Phase 1 completion
