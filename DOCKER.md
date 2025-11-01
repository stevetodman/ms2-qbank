# MS2 QBank Docker Setup

This document explains how to run the MS2 QBank platform using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available for Docker
- At least 10GB disk space

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd ms2-qbank

# Copy environment variables
cp .env.example .env

# Edit .env and update values (especially SECRET_KEY for production)
nano .env
```

### 2. Build and Start All Services

```bash
# Build all images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 3. Verify Services

```bash
# Check all services are running
docker-compose ps

# Test each service
curl http://localhost:8000/docs  # Users API
curl http://localhost:8001/docs  # Flashcards API
curl http://localhost:8002/docs  # Assessments API
curl http://localhost:8003/docs  # Videos API
curl http://localhost:8004/docs  # Library API
curl http://localhost:8005/docs  # Planner API
curl http://localhost:8006/docs  # Questions API
curl http://localhost:8007/docs  # Reviews API
curl http://localhost:8008/docs  # Analytics API

# Access frontend
open http://localhost:5173
```

## Architecture

The Docker setup includes:

### Backend Services (9 microservices)
- **Users** (port 8000): Authentication & user profiles
- **Flashcards** (port 8001): Spaced repetition flashcards
- **Assessments** (port 8002): Self-assessment exams
- **Videos** (port 8003): Video library & playlists
- **Library** (port 8004): Medical articles & notebooks
- **Planner** (port 8005): Study scheduling
- **Questions** (port 8006): Question bank
- **Reviews** (port 8007): Review workflows
- **Analytics** (port 8008): Performance tracking

### Supporting Services
- **PostgreSQL** (port 5432): Primary database (future)
- **Redis** (port 6379): Caching layer (future)
- **Frontend** (port 5173): React application with Nginx

## Development Mode

For active development with hot reload:

```bash
# Start services in development mode (already configured)
docker-compose up

# Watch logs for specific service
docker-compose logs -f users

# Rebuild after code changes (if needed)
docker-compose up --build users
```

All services are configured with volume mounts for hot reload:
- `./src:/app/src` - Backend code
- `./data:/app/data` - Databases

## Production Deployment

### 1. Update Environment Variables

```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env file
SECRET_KEY=<generated-key>
POSTGRES_PASSWORD=<secure-password>
DEBUG=false
CORS_ORIGINS=https://yourdomain.com
```

### 2. Switch to PostgreSQL

Update all service DATABASE_URLs in docker-compose.yml:

```yaml
environment:
  - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/ms2qbank_users
```

### 3. Build Production Images

```bash
# Build optimized images
docker-compose -f docker-compose.prod.yml build

# Start in production mode
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Setup SSL/TLS

For production, use a reverse proxy like Nginx or Traefik with Let's Encrypt:

```bash
# Example with Traefik
docker run -d \
  --name traefik \
  -p 80:80 \
  -p 443:443 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v letsencrypt:/letsencrypt \
  traefik:v2.10 \
  --api.insecure=true \
  --providers.docker=true \
  --entrypoints.web.address=:80 \
  --entrypoints.websecure.address=:443 \
  --certificatesresolvers.myresolver.acme.tlschallenge=true \
  --certificatesresolvers.myresolver.acme.email=your@email.com \
  --certificatesresolvers.myresolver.acme.storage=/letsencrypt/acme.json
```

## Common Operations

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f users

# Last 100 lines
docker-compose logs --tail=100

# Follow new logs only
docker-compose logs -f --tail=0
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart users

# Restart after code changes
docker-compose up -d --no-deps --build users
```

### Database Operations

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres

# Backup database
docker-compose exec postgres pg_dump -U postgres ms2qbank_users > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres ms2qbank_users < backup.sql

# View database logs
docker-compose logs postgres
```

### Scale Services

```bash
# Run 3 instances of users service behind a load balancer
docker-compose up -d --scale users=3

# Note: Requires load balancer configuration
```

### Clean Up

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data!)
docker-compose down -v

# Remove all images
docker-compose down --rmi all

# Remove everything including orphaned containers
docker-compose down -v --remove-orphans
```

## Troubleshooting

### Service won't start

```bash
# Check service logs
docker-compose logs users

# Check if port is already in use
lsof -i :8000

# Restart with fresh build
docker-compose down
docker-compose up --build
```

### Database connection errors

```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Test connection
docker-compose exec users python -c "from sqlmodel import create_engine; engine = create_engine('sqlite:///data/users.db'); print('Connected!')"
```

### Container keeps restarting

```bash
# Check health status
docker-compose ps

# View recent logs
docker-compose logs --tail=50 users

# Run service interactively
docker-compose run --rm users sh
```

### Out of disk space

```bash
# Check Docker disk usage
docker system df

# Clean up unused data
docker system prune -a --volumes

# Remove unused images
docker image prune -a
```

### Slow performance

```bash
# Check resource usage
docker stats

# Increase memory limit in docker-compose.yml
services:
  users:
    deploy:
      resources:
        limits:
          memory: 512M
```

## Running Tests in Docker

```bash
# Run backend tests
docker-compose exec users pytest tests/

# Run tests with coverage
docker-compose exec users pytest --cov=src --cov-report=html

# Run specific test file
docker-compose exec users pytest tests/test_users.py

# Run frontend tests
docker-compose exec frontend npm test
```

## Performance Optimization

### 1. Use BuildKit

```bash
# Enable BuildKit for faster builds
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

docker-compose build
```

### 2. Multi-stage Builds

The Dockerfiles use multi-stage builds to reduce image size:
- Builder stage: Installs all dependencies
- Production stage: Only copies necessary files

### 3. Layer Caching

Order Dockerfile commands for better caching:
1. Install system dependencies (rarely changes)
2. Copy requirements.txt and install packages (changes occasionally)
3. Copy source code (changes frequently)

### 4. Use .dockerignore

Ensure `.dockerignore` excludes:
- `__pycache__`
- `.git`
- `node_modules`
- `*.db` files (use volumes instead)

## Monitoring

### Health Checks

All services have health checks configured:

```bash
# View health status
docker-compose ps

# Test specific health endpoint
curl http://localhost:8000/health
```

### Resource Monitoring

```bash
# Real-time stats
docker stats

# Export stats to file
docker stats --no-stream > stats.txt
```

## Security Best Practices

1. **Never commit `.env` file** - Contains secrets
2. **Use secrets management** - Docker Swarm secrets or Kubernetes secrets
3. **Run as non-root user** - Add `USER` directive in Dockerfile
4. **Scan images for vulnerabilities**:
   ```bash
   docker scan ms2qbank-users
   ```
5. **Keep base images updated**:
   ```bash
   docker-compose pull
   docker-compose up -d
   ```
6. **Limit resource usage** - Set memory/CPU limits
7. **Use private registry** - Don't push images to public registries

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/docker.yml
name: Docker Build and Push

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: docker/setup-buildx-action@v2
      - uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}/users:latest
```

## Networking

### Container Communication

Services communicate via Docker network `ms2qbank`:
- Use service names as hostnames (e.g., `http://users:8000`)
- No need for `localhost` or IP addresses

### External Access

```bash
# Access from host machine
curl http://localhost:8000

# Access from another container
curl http://users:8000
```

## Volume Management

### Data Persistence

Volumes are defined for:
- `postgres_data`: PostgreSQL database files
- `./data`: SQLite databases (development)
- `./src`: Source code (hot reload)

### Backup Volumes

```bash
# Backup volume
docker run --rm \
  -v ms2qbank_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres-backup.tar.gz /data

# Restore volume
docker run --rm \
  -v ms2qbank_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/postgres-backup.tar.gz -C /
```

## Useful Docker Commands

```bash
# Execute command in running container
docker-compose exec users bash

# Run one-off command
docker-compose run --rm users python manage.py

# View container processes
docker-compose top

# View container config
docker-compose config

# Validate docker-compose.yml
docker-compose config --quiet

# Pull latest images
docker-compose pull

# Build without cache
docker-compose build --no-cache
```

## Support

For issues or questions:
1. Check service logs: `docker-compose logs <service>`
2. Check GitHub issues
3. Review this documentation
4. Contact maintainers

## License

See LICENSE file in repository root.
