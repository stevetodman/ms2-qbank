# CI/CD Documentation

This document describes the Continuous Integration and Continuous Deployment (CI/CD) pipeline for MS2 QBank.

## Overview

The MS2 QBank project uses GitHub Actions for automated testing, building, and deployment. The CI/CD pipeline ensures code quality, security, and reliability before changes are merged.

## Workflows

### 1. CI - Tests and Linting (`ci.yml`)

**Triggers:**
- Push to `main` branch
- Pull requests to `main` branch

**Jobs:**

#### Backend Tests
- Runs all Python tests with pytest
- Uses PostgreSQL service container for database tests
- Tests all microservices:
  - User authentication
  - Flashcards
  - Assessments
  - Analytics
  - Library
  - Planner
  - Videos
  - Reviews
- Generates code coverage reports
- Uploads coverage to Codecov (requires `CODECOV_TOKEN` secret)

#### Python Linting
- **Ruff**: Fast Python linter for code quality
- **Black**: Code formatter checker
- **isort**: Import statement organizer
- **mypy**: Static type checker

#### Frontend Tests
- TypeScript type checking
- ESLint linting
- Unit tests with Jest
- Production build verification

#### Integration Tests
- Builds all Docker images
- Starts entire stack with `docker compose`
- Health checks all services
- Verifies inter-service communication

**Required Secrets:**
- `CODECOV_TOKEN` (optional, for code coverage)

---

### 2. Docker Build and Push (`docker-build.yml`)

**Triggers:**
- Push to `main` branch
- Git tags matching `v*.*.*` pattern
- Manual workflow dispatch

**Jobs:**

#### Build and Push Backend Services
- Builds Docker images for all 9 microservices
- Pushes to GitHub Container Registry (ghcr.io)
- Uses layer caching for faster builds
- Tags images with:
  - Branch name (e.g., `main`)
  - Git SHA (e.g., `main-abc1234`)
  - Semantic version (e.g., `v1.0.0`, `1.0`, `1`)
  - `latest` tag for main branch

#### Build and Push Frontend
- Builds optimized production frontend
- Multi-stage build with Nginx
- Same tagging strategy as backend

**Image Naming:**
- Backend: `ghcr.io/<username>/ms2-qbank-<service>:latest`
- Frontend: `ghcr.io/<username>/ms2-qbank-frontend:latest`

**Required Permissions:**
- `packages: write` (automatically granted by GitHub)

---

### 3. Security Scanning (`security.yml`)

**Triggers:**
- Push to `main` branch
- Pull requests to `main` branch
- Daily schedule (2 AM UTC)

**Jobs:**

#### Dependency Vulnerability Scan
- **Safety**: Checks Python dependencies against vulnerability database
- **pip-audit**: Audits Python packages for known vulnerabilities
- **npm audit**: Checks frontend dependencies

#### Secret Scanning
- **TruffleHog**: Scans for accidentally committed secrets
- Checks entire git history
- Finds API keys, tokens, passwords, etc.

#### CodeQL Analysis
- GitHub's semantic code analysis
- Detects security vulnerabilities in code
- Supports Python and JavaScript
- Runs security-extended and quality queries

#### Docker Image Scanning
- **Trivy**: Comprehensive vulnerability scanner
- Scans base images and dependencies
- Checks for HIGH and CRITICAL vulnerabilities
- Uploads results to GitHub Security tab

**Security Findings:**
- View in GitHub Security tab → Code scanning alerts
- Automated vulnerability alerts via Dependabot

---

## Local Testing

### Run Tests Locally

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run specific test file
pytest tests/test_user_auth.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run only fast tests (skip slow tests)
pytest -m "not slow"

# Run only integration tests
pytest -m integration
```

### Linting Locally

```bash
# Run all linters
ruff check src/ tests/
black --check src/ tests/
isort --check-only src/ tests/
mypy src/

# Auto-fix formatting
black src/ tests/
isort src/ tests/

# Fix auto-fixable Ruff issues
ruff check --fix src/ tests/
```

### Build Docker Images Locally

```bash
# Build all services
docker compose build

# Build specific service
docker compose build users

# Start all services
docker compose up -d

# Check health
docker compose ps
curl http://localhost:8000/health
```

---

## Configuration

### pytest.ini

The `pytest.ini` file configures:
- Test discovery patterns
- Coverage settings
- Test markers (slow, integration, unit, api, database, auth)
- Logging configuration
- Warning filters

### Test Markers

Use markers to categorize tests:

```python
import pytest

@pytest.mark.slow
def test_large_dataset():
    """This test takes a long time"""
    pass

@pytest.mark.integration
def test_api_endpoint():
    """This tests multiple components together"""
    pass
```

Run specific markers:
```bash
# Skip slow tests
pytest -m "not slow"

# Only integration tests
pytest -m integration

# Only API tests
pytest -m api
```

---

## Required GitHub Secrets

To enable all features, add these secrets to your repository:

### Optional Secrets

1. **CODECOV_TOKEN**
   - Sign up at https://codecov.io
   - Link your repository
   - Copy token to GitHub Secrets
   - Enables code coverage tracking

### Automatically Available Secrets

These are provided by GitHub:
- `GITHUB_TOKEN` - For pushing Docker images
- `github.actor` - Current GitHub username

---

## Continuous Deployment (Future)

### Staging Deployment

To enable automatic deployment to staging:

1. Create a new workflow file `.github/workflows/deploy-staging.yml`
2. Add deployment steps after successful CI
3. Configure staging environment secrets

Example:
```yaml
deploy-staging:
  needs: [backend-tests, frontend-tests, integration-tests]
  runs-on: ubuntu-latest
  environment: staging
  steps:
    - name: Deploy to staging
      run: |
        # Your deployment commands
        ssh user@staging-server "docker compose pull && docker compose up -d"
```

### Production Deployment

Production deployment should be manual or triggered by git tags:

```yaml
on:
  push:
    tags:
      - 'v*.*.*'
```

---

## Troubleshooting

### Tests Failing in CI but Pass Locally

**Issue**: PostgreSQL version mismatch
- CI uses PostgreSQL 15-alpine
- Check your local PostgreSQL version
- Update `docker-compose.yml` to match CI

**Issue**: Environment variables not set
- CI sets `DATABASE_URL`, `SECRET_KEY`
- Check `.github/workflows/ci.yml` env section
- Ensure tests use correct env vars

### Docker Build Failures

**Issue**: Out of disk space
- GitHub runners have limited disk space
- Use `docker system prune` in workflow
- Enable layer caching with `cache-from` and `cache-to`

**Issue**: Slow builds
- Enable Docker Buildx caching
- Use multi-stage builds
- Cache pip/npm dependencies

### Security Scan Failures

**Issue**: False positives in TruffleHog
- Add `.trufflehog-ignore.yml` to exclude specific findings
- Use `--only-verified` flag to reduce noise

**Issue**: Outdated dependencies flagged
- Run `pip-audit -r requirements.txt` locally
- Update dependencies: `pip install -U <package>`
- Check if newer versions fix vulnerabilities

---

## Best Practices

### Pull Request Workflow

1. Create feature branch from `main`
2. Make changes
3. Run tests locally: `pytest`
4. Run linters locally: `ruff check . && black --check .`
5. Push to GitHub
6. GitHub Actions runs automatically
7. Review CI results
8. Fix any failures
9. Request code review
10. Merge when CI passes ✅

### Keeping CI Fast

- Use parallel jobs where possible
- Cache dependencies (pip, npm, Docker layers)
- Skip slow tests in PR checks (run on merge to main)
- Use `continue-on-error: true` for non-critical checks

### Security

- Never commit secrets (keys, tokens, passwords)
- Use GitHub Secrets for sensitive data
- Review security scan results weekly
- Update dependencies regularly
- Enable Dependabot for automated dependency updates

---

## Monitoring CI/CD

### GitHub Actions Dashboard

View workflow runs:
1. Go to repository → Actions tab
2. Click on workflow name
3. View recent runs and results

### Status Badges

Add to README.md:

```markdown
![CI Status](https://github.com/<username>/ms2-qbank/workflows/CI%20-%20Tests%20and%20Linting/badge.svg)
![Security](https://github.com/<username>/ms2-qbank/workflows/Security%20Scanning/badge.svg)
[![codecov](https://codecov.io/gh/<username>/ms2-qbank/branch/main/graph/badge.svg)](https://codecov.io/gh/<username>/ms2-qbank)
```

### Notifications

Configure notifications in GitHub Settings:
- Settings → Notifications
- Email on workflow failure
- Slack/Discord webhooks (optional)

---

## Cost Optimization

GitHub Actions minutes:
- **Free tier**: 2,000 minutes/month for private repos
- **Public repos**: Unlimited minutes

Tips to reduce usage:
1. Use self-hosted runners (advanced)
2. Cache dependencies aggressively
3. Skip redundant jobs (e.g., linting on docs-only changes)
4. Use `paths` filter to run only when relevant files change

Example:
```yaml
on:
  push:
    paths:
      - 'src/**'
      - 'tests/**'
      - 'requirements.txt'
```

---

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [CodeQL Documentation](https://codeql.github.com/docs/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Ruff Linter](https://github.com/astral-sh/ruff)
