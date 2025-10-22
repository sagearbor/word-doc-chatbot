# Docker Deployment Guide

This guide explains how to deploy the Word Document Chatbot using Docker and Docker Compose.

## Table of Contents
- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Deployment Scenarios](#deployment-scenarios)
- [Commands Reference](#commands-reference)
- [Troubleshooting](#troubleshooting)
- [Production Considerations](#production-considerations)

---

## Quick Start

### 1. Clone and Navigate
```bash
git clone https://github.com/sagearbor/word-doc-chatbot.git
cd word-doc-chatbot
```

### 2. Configure Environment
```bash
# Create backend environment file
cp backend/.env.example backend/.env
# Edit backend/.env and set your AI provider API keys

# For path-based deployment (e.g., /sageapp04/)
export BASE_URL_PATH=/sageapp04
```

### 3. Build and Run
```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Access Application
- **Local testing (no NGINX)**: http://localhost:8501
- **With NGINX helper**: http://localhost:3004
- **Production**: https://yourdomain.com/sageapp04/ (via main NGINX)

---

## Architecture Overview

### Services

The Docker deployment consists of three services:

```
┌─────────────────────────────────────────────────────────────┐
│                      Main NGINX (IT-managed)                │
│              https://aidemo.dcri.duke.edu/sageapp04/        │
└────────────────────────┬────────────────────────────────────┘
                         │ strips /sageapp04
                         ↓
┌─────────────────────────────────────────────────────────────┐
│            NGINX Helper Container (port 3004)               │
│         Restores /sageapp04 prefix for Streamlit           │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         ↓                               ↓
┌──────────────────┐            ┌──────────────────┐
│  Frontend        │            │  Backend         │
│  (Streamlit)     │───────────→│  (FastAPI)       │
│  Port: 8501      │  API calls │  Port: 8000      │
└──────────────────┘            └──────────────────┘
```

**1. Backend Container**
- FastAPI application
- Handles document processing and LLM interactions
- Exposed on `127.0.0.1:8004` (or port 8000 inside container)
- Health check: `http://localhost:8004/`

**2. Frontend Container**
- Streamlit UI application
- Communicates with backend via Docker network
- Configured with BASE_URL_PATH for reverse proxy
- Health check: `http://localhost:8501/_stcore/health`

**3. NGINX Helper Container** *(optional, for path-based deployment)*
- Lightweight Alpine NGINX
- Fixes path mismatch between main NGINX and Streamlit
- Exposed on `127.0.0.1:3004`
- Only needed for path-prefix deployments (e.g., `/sageapp04/`)

---

## Prerequisites

### Required Software
- Docker 20.10+
- Docker Compose 2.0+

### System Requirements
- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 10GB free space

### API Keys
You'll need at least one AI provider API key:
- **OpenAI**: Get from https://platform.openai.com/api-keys
- **Azure OpenAI**: From Azure Portal
- **Anthropic**: From https://console.anthropic.com/
- **Google AI**: From Google Cloud Console

---

## Configuration

### 1. Backend Configuration

Create `backend/.env` from the template:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:

```bash
# AI Provider (choose one: openai, azure_openai, anthropic, google)
AI_PROVIDER=openai

# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your-actual-key-here

# OR Azure OpenAI Configuration
# AZURE_OPENAI_API_KEY=your-key
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
# AZURE_OPENAI_API_VERSION=2024-02-15-preview
# AZURE_OPENAI_DEPLOYMENT=gpt-4

# OR Anthropic Configuration
# ANTHROPIC_API_KEY=sk-ant-your-key

# OR Google Configuration
# GOOGLE_API_KEY=AIza-your-key

# Application Settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

### 2. Frontend Configuration

For path-based deployment, set environment variable:

```bash
# In docker-compose.yml or as environment variable
BASE_URL_PATH=/sageapp04
```

For root deployment:

```bash
# Leave empty or omit
BASE_URL_PATH=
```

### 3. NGINX Helper Configuration

For path-based deployment, ensure `nginx-helper-docker.conf` has the correct rewrite rule:

```nginx
# For /sageapp04/
rewrite ^/(.*)$ /sageapp04/$1 break;

# For /myapp/
# rewrite ^/(.*)$ /myapp/$1 break;
```

---

## Deployment Scenarios

### Scenario 1: Local Development (No NGINX)

**Use case**: Local testing and development

**Configuration**:
```bash
# docker-compose.yml - uncomment frontend ports
services:
  frontend:
    ports:
      - "8501:8501"

  # Comment out nginx-helper service
  # nginx-helper:
  #   ...
```

**Start**:
```bash
docker-compose up -d backend frontend
```

**Access**: http://localhost:8501

---

### Scenario 2: POC/Demo with Path Prefix (e.g., /sageapp04/)

**Use case**: Multiple apps on shared VM with NGINX

**Configuration**:
```bash
# Set environment variable
export BASE_URL_PATH=/sageapp04

# Ensure backend/.env has AI credentials
```

**Start**:
```bash
docker-compose build
docker-compose up -d
```

**Access**:
- Via NGINX helper: http://localhost:3004
- Via main NGINX: https://aidemo.dcri.duke.edu/sageapp04/

**Main NGINX config** (managed by IT):
```nginx
location = /sageapp04  { return 301 /sageapp04/; }
location /sageapp04/  { proxy_pass http://127.0.0.1:3004/; }
```

---

### Scenario 3: Production (Dedicated Domain, No Path)

**Use case**: Dedicated domain like `https://docbot.company.com`

**Configuration**:
```bash
# Remove BASE_URL_PATH or set to empty
export BASE_URL_PATH=

# Update docker-compose.yml - expose frontend directly
services:
  frontend:
    ports:
      - "127.0.0.1:3004:8501"  # Or any port

  # Remove nginx-helper service entirely
```

**Start**:
```bash
docker-compose up -d backend frontend
```

**Main NGINX config**:
```nginx
server {
    listen 443 ssl;
    server_name docbot.company.com;

    location / {
        proxy_pass http://127.0.0.1:3004;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Standard headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_buffering off;
        proxy_read_timeout 86400;
    }
}
```

---

### Scenario 4: Azure App Service

**Use case**: Deploying to Azure Container Instances or App Service

**Configuration**:
```bash
# Set in Azure App Service Configuration
BASE_URL_PATH=/
BACKEND_URL=http://backend-app.azurewebsites.net
AI_PROVIDER=azure_openai
AZURE_OPENAI_API_KEY=<from-key-vault>
```

**Notes**:
- Azure App Service provides its own reverse proxy
- Set `STREAMLIT_PORT=8000` (Azure expects port 8000)
- Use Azure Key Vault for API keys
- Remove nginx-helper service

---

## Commands Reference

### Build and Start

```bash
# Build all images
docker-compose build

# Build specific service
docker-compose build backend
docker-compose build frontend

# Build without cache (for clean rebuild)
docker-compose build --no-cache

# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d backend frontend

# Start with logs visible
docker-compose up

# Start and rebuild if needed
docker-compose up -d --build
```

### Status and Logs

```bash
# Check status
docker-compose ps

# View logs (all services)
docker-compose logs -f

# View logs (specific service)
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f nginx-helper

# View last 100 lines
docker-compose logs --tail=100

# View logs since timestamp
docker-compose logs --since=2024-01-01T00:00:00
```

### Stop and Cleanup

```bash
# Stop services (keeps containers)
docker-compose stop

# Start stopped services
docker-compose start

# Restart services
docker-compose restart

# Stop and remove containers
docker-compose down

# Stop, remove containers, and remove volumes
docker-compose down -v

# Remove everything including images
docker-compose down -v --rmi all

# Remove orphan containers
docker-compose down --remove-orphans
```

### Debugging

```bash
# Execute command in running container
docker-compose exec backend bash
docker-compose exec frontend sh

# Check environment variables
docker-compose exec backend env
docker-compose exec frontend env

# Test backend health
docker-compose exec backend curl http://localhost:8000/

# Test frontend health
docker-compose exec frontend curl http://localhost:8501/_stcore/health

# Inspect container
docker inspect word-doc-chatbot-backend
docker inspect word-doc-chatbot-frontend

# Check resource usage
docker stats

# View network details
docker network inspect word-doc-chatbot-network
```

### Updates and Maintenance

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# View image sizes
docker images | grep word-doc-chatbot

# Clean up old images
docker image prune -a

# Clean up everything Docker (use with caution!)
docker system prune -a
```

---

## Troubleshooting

### Issue: Containers won't start

**Check logs**:
```bash
docker-compose logs backend
docker-compose logs frontend
```

**Common causes**:
- Missing API keys in `backend/.env`
- Port already in use
- Insufficient resources

**Solutions**:
```bash
# Check ports
sudo lsof -i :8004
sudo lsof -i :3004

# Check resources
docker system df
docker stats

# Restart Docker daemon
sudo systemctl restart docker
```

### Issue: Backend returns 500 errors

**Check backend logs**:
```bash
docker-compose logs -f backend
```

**Common causes**:
- Invalid API key
- AI provider service down
- Missing dependencies

**Solutions**:
```bash
# Verify API key
docker-compose exec backend env | grep API_KEY

# Test API connectivity
docker-compose exec backend curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Rebuild backend
docker-compose build --no-cache backend
docker-compose up -d backend
```

### Issue: Frontend can't connect to backend

**Symptoms**:
- "Connection Error" in Streamlit UI
- "Is the backend server running?" message

**Check**:
```bash
# Verify backend is running
docker-compose ps backend

# Test backend from frontend container
docker-compose exec frontend curl http://backend:8000/

# Check network
docker network inspect word-doc-chatbot-network
```

**Solutions**:
```bash
# Ensure both services on same network
# Check docker-compose.yml networks section

# Restart services
docker-compose restart backend frontend
```

### Issue: WebSocket connection failed

**Symptoms**:
- App loads but appears frozen
- Browser console shows WebSocket errors

**Check**:
```bash
# Verify BASE_URL_PATH matches NGINX config
docker-compose exec frontend env | grep BASE_URL_PATH

# Check NGINX helper logs
docker-compose logs nginx-helper
```

**Solutions**:
- Ensure `BASE_URL_PATH` environment variable is set correctly
- Verify nginx-helper.conf rewrite rule matches path
- Check main NGINX configuration

### Issue: High memory usage

**Check**:
```bash
docker stats
```

**Solutions**:
```bash
# Set memory limits in docker-compose.yml
services:
  backend:
    mem_limit: 2g
  frontend:
    mem_limit: 1g
```

---

## Production Considerations

### Security

**1. Use secrets management**:
```yaml
# docker-compose.yml
services:
  backend:
    secrets:
      - openai_api_key

secrets:
  openai_api_key:
    file: ./secrets/openai_key.txt
```

**2. Run as non-root** (already configured in Dockerfile):
```dockerfile
USER appuser
```

**3. Limit network exposure**:
```yaml
ports:
  - "127.0.0.1:8004:8000"  # Localhost only
```

**4. Use environment-specific configs**:
```bash
# .env.production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
```

### Performance

**1. Resource limits**:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

**2. Health checks**:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

**3. Restart policy**:
```yaml
restart: unless-stopped
```

### Monitoring

**1. Enable logging**:
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

**2. Export logs**:
```bash
# Export to file
docker-compose logs > logs_$(date +%Y%m%d).txt

# Send to logging service (example with syslog)
logging:
  driver: syslog
  options:
    syslog-address: "tcp://logging-server:514"
```

**3. Metrics collection**:
```bash
# Use Prometheus + cAdvisor for metrics
# See: https://github.com/google/cadvisor
```

### Backups

**1. Volume backups**:
```bash
# Backup temp files volume
docker run --rm -v word-doc-chatbot-backend-temp:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/backend-temp-$(date +%Y%m%d).tar.gz /data
```

**2. Database backups** (if you add a database later):
```bash
# Example for PostgreSQL
docker-compose exec db pg_dump -U user dbname > backup.sql
```

### Updates

**Zero-downtime updates**:
```bash
# Build new images
docker-compose build

# Rolling update (one service at a time)
docker-compose up -d --no-deps backend
# Wait and verify
docker-compose up -d --no-deps frontend
```

---

## Environment Variables Reference

### Backend
- `AI_PROVIDER`: AI provider to use (openai, azure_openai, anthropic, google)
- `OPENAI_API_KEY`: OpenAI API key
- `AZURE_OPENAI_*`: Azure OpenAI configuration
- `ANTHROPIC_API_KEY`: Anthropic API key
- `GOOGLE_API_KEY`: Google AI API key
- `ENVIRONMENT`: Environment name (development, production)
- `DEBUG`: Enable debug mode (true/false)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Frontend
- `BACKEND_URL`: Backend API URL (default: http://backend:8000)
- `BASE_URL_PATH`: URL path prefix (e.g., /sageapp04 or empty)
- `STREAMLIT_PORT`: Streamlit server port (default: 8501)
- `SERVER_ADDRESS`: Server bind address (default: 0.0.0.0)

---

## Additional Resources

- **NGINX Configuration**: See `NGINX_DEPLOYMENT_GUIDE.md`
- **Docker Compose Docs**: https://docs.docker.com/compose/
- **Streamlit Docker Deployment**: https://docs.streamlit.io/knowledge-base/deploy/deploy-streamlit-using-docker
- **FastAPI Docker Deployment**: https://fastapi.tiangolo.com/deployment/docker/

---

## Quick Reference Card

```bash
# Start everything
docker-compose up -d

# View logs
docker-compose logs -f

# Stop everything
docker-compose down

# Rebuild after code changes
docker-compose build && docker-compose up -d

# Check status
docker-compose ps

# Access shell
docker-compose exec backend bash
docker-compose exec frontend sh

# View resource usage
docker stats

# Clean up
docker-compose down -v
docker system prune -a
```

---

**Need help?** Check the troubleshooting section or file an issue on GitHub.
