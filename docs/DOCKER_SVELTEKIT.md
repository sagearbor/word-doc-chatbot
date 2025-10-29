# SvelteKit Single-Container Docker Deployment Guide

This guide covers deploying the Word Document Chatbot as a single Docker container containing both the SvelteKit frontend and FastAPI backend.

## Architecture Overview

**Single-Container Design:**
- **Stage 1 (Build)**: Compile SvelteKit frontend to static files using Node.js
- **Stage 2 (Runtime)**: Python container serving both FastAPI API and static SvelteKit files
- **Benefits**: Simplified deployment, single container to manage, no inter-container networking
- **Tradeoffs**: Frontend changes require full rebuild (both stages)

## Quick Start

### 1. Prerequisites

- Docker installed and running
- `.env` file configured with API keys
- Project root directory: `/dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot/`

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env to add your API keys
# Required variables:
#   - AI_PROVIDER (e.g., azure_openai, openai, anthropic)
#   - Corresponding API keys (e.g., AZURE_OPENAI_API_KEY)
#   - BASE_URL_PATH (default: /sageapp04)
```

### 3. Build Docker Image

```bash
# From project root
cd /dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot

# Build with default settings (BASE_URL_PATH=/sageapp04)
./scripts/build-docker.sh

# Or build with custom BASE_URL_PATH
BASE_URL_PATH=/my-custom-path ./scripts/build-docker.sh
```

**Build process:**
1. Stage 1: Installs Node.js dependencies and builds SvelteKit static site
2. Stage 2: Copies static files and Python backend into Python container
3. Creates non-root user (appuser) for security
4. Sets up health check endpoint
5. Tags image as `word-chatbot:sveltekit` and `word-chatbot:latest`

### 4. Run Container

```bash
# Start container with auto-restart
./scripts/run-docker.sh

# Container will:
#   - Start FastAPI on port 8000 (internal)
#   - Map to host port 3004
#   - Serve frontend at http://localhost:3004/sageapp04/
#   - Serve API docs at http://localhost:3004/docs
#   - Auto-restart unless stopped manually
```

### 5. Verify Deployment

```bash
# Check container status
docker ps | grep word-chatbot

# View logs
docker logs -f word-chatbot-sveltekit

# Test health endpoint
curl http://localhost:3004/health

# Test frontend (in browser)
# http://localhost:3004/sageapp04/
```

## Management Commands

### View Logs
```bash
# Follow logs in real-time
docker logs -f word-chatbot-sveltekit

# View last 100 lines
docker logs --tail 100 word-chatbot-sveltekit

# View logs with timestamps
docker logs -t word-chatbot-sveltekit
```

### Stop Container
```bash
# Stop gracefully
./scripts/stop-docker.sh

# Or manually
docker stop word-chatbot-sveltekit
```

### Restart Container
```bash
# If container exists but is stopped
docker start word-chatbot-sveltekit

# Or stop and start fresh
docker restart word-chatbot-sveltekit
```

### Remove Container
```bash
# Remove stopped container
docker rm word-chatbot-sveltekit

# Force remove (even if running)
docker rm -f word-chatbot-sveltekit
```

### Rebuild After Changes
```bash
# Frontend or backend code changed
./scripts/build-docker.sh

# Stop old container
docker stop word-chatbot-sveltekit
docker rm word-chatbot-sveltekit

# Start new container
./scripts/run-docker.sh
```

## NGINX Reverse Proxy Configuration

### Option 1: Without Trailing Slash (Recommended)

NGINX keeps the path prefix, FastAPI sees `/sageapp04/...`:

```nginx
location /sageapp04 {
    proxy_pass http://127.0.0.1:3004;
    proxy_http_version 1.1;

    # WebSocket support
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";

    # Standard headers
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Timeouts
    proxy_read_timeout 300s;
    proxy_connect_timeout 75s;
}
```

**Requirements:**
- `BASE_URL_PATH=/sageapp04` in .env (used at build time)
- FastAPI must mount static files at `/sageapp04/`
- No nginx-helper container needed

### Option 2: With Trailing Slash (Legacy)

NGINX strips the prefix, requires nginx-helper to restore it:

```nginx
location /sageapp04/ {
    proxy_pass http://127.0.0.1:3004/;  # Note trailing slash
    # ... same headers as above
}
```

**Requirements:**
- nginx-helper container to restore prefix
- More complex deployment
- Not recommended for new deployments

## Environment Variables

### Build-Time Variables

Set before running `./scripts/build-docker.sh`:

```bash
# Base URL path for reverse proxy
BASE_URL_PATH=/sageapp04

# Build with custom path
BASE_URL_PATH=/my-app ./scripts/build-docker.sh
```

### Runtime Variables

Set in `.env` file before running `./scripts/run-docker.sh`:

```bash
# AI Provider Configuration
AI_PROVIDER=azure_openai
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEFAULT_DEPLOYMENT_NAME=gpt-4o-mini

# Alternative providers
# AI_PROVIDER=openai
# OPENAI_API_KEY=sk-...

# AI_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-...

# Application Settings
ENVIRONMENT=production
DEBUG_MODE=false
APP_TITLE=Word Document Chatbot

# File Upload Settings
MAX_FILE_SIZE_MB=10
ALLOWED_FILE_TYPES=.docx
```

## Troubleshooting

### Container Won't Start

```bash
# Check container logs
docker logs word-chatbot-sveltekit

# Common issues:
# 1. Missing .env file
#    Solution: cp .env.example .env && edit .env

# 2. Invalid API keys
#    Solution: Verify API keys in .env

# 3. Port 3004 already in use
#    Solution: Edit scripts/run-docker.sh to use different port
```

### Frontend Not Loading

```bash
# Verify static files were built
docker exec word-chatbot-sveltekit ls -la /app/static

# Check frontend path in browser
# Should be: http://localhost:3004/sageapp04/
# Not: http://localhost:3004/

# Verify BASE_URL_PATH in build
docker inspect word-chatbot-sveltekit | grep BASE_URL_PATH
```

### API Calls Failing

```bash
# Check backend logs
docker logs word-chatbot-sveltekit | grep ERROR

# Test health endpoint
curl http://localhost:3004/health

# Test API docs
curl http://localhost:3004/docs

# Verify environment variables loaded
docker exec word-chatbot-sveltekit env | grep AI_PROVIDER
```

### NGINX 404 Errors

```bash
# Verify NGINX configuration
nginx -t

# Check NGINX logs
tail -f /var/log/nginx/error.log

# Ensure location block matches BASE_URL_PATH
# If BASE_URL_PATH=/sageapp04, use:
#   location /sageapp04 { proxy_pass http://127.0.0.1:3004; }
```

### Rebuild Not Reflecting Changes

```bash
# Full rebuild process
docker stop word-chatbot-sveltekit
docker rm word-chatbot-sveltekit
docker rmi word-chatbot:sveltekit

# Clear build cache if needed
docker builder prune

# Rebuild from scratch
./scripts/build-docker.sh
./scripts/run-docker.sh
```

## File Structure

```
/dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot/
├── Dockerfile.sveltekit          # Multi-stage Dockerfile
├── .dockerignore                  # Files excluded from build
├── .env                           # Runtime configuration (create from .env.example)
├── .env.example                   # Example configuration
├── requirements.txt               # Python dependencies
├── backend/                       # FastAPI backend code
│   ├── main.py                   # API endpoints + static file serving
│   ├── config.py                 # Configuration management
│   └── ...
├── frontend-new/                  # SvelteKit frontend code
│   ├── package.json              # Node.js dependencies
│   ├── svelte.config.js          # SvelteKit configuration (adapter-static)
│   └── src/                      # Frontend source code
└── scripts/
    ├── build-docker.sh           # Build Docker image
    ├── run-docker.sh             # Run Docker container
    └── stop-docker.sh            # Stop Docker container
```

## Security Considerations

### Built-In Security Features

1. **Non-Root User**: Container runs as `appuser` (UID 1000)
2. **Health Checks**: Automatic monitoring via Docker healthcheck
3. **Port Binding**: Binds to 127.0.0.1 only (not exposed to network)
4. **Minimal Image**: Uses Python slim base image
5. **No Secrets in Image**: API keys loaded from .env at runtime

### Production Recommendations

```bash
# 1. Use secrets management instead of .env
docker secret create api_key /path/to/api_key.txt

# 2. Enable Docker security features
docker run \
  --read-only \
  --tmpfs /tmp \
  --security-opt=no-new-privileges \
  --cap-drop ALL \
  --name word-chatbot-sveltekit \
  -p 127.0.0.1:3004:8000 \
  --env-file .env \
  word-chatbot:sveltekit

# 3. Use HTTPS with SSL certificates in NGINX
# 4. Implement rate limiting in NGINX
# 5. Regular security updates
docker pull python:3.11-slim
./scripts/build-docker.sh
```

## Performance Optimization

### Build Optimization

```bash
# Use BuildKit for faster builds
DOCKER_BUILDKIT=1 ./scripts/build-docker.sh

# Multi-platform builds (if needed)
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --file Dockerfile.sveltekit \
  --tag word-chatbot:sveltekit \
  .
```

### Runtime Optimization

```bash
# Allocate more resources
docker run \
  --cpus="2.0" \
  --memory="2g" \
  --name word-chatbot-sveltekit \
  -p 127.0.0.1:3004:8000 \
  --env-file .env \
  word-chatbot:sveltekit

# Monitor resource usage
docker stats word-chatbot-sveltekit
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: ./scripts/build-docker.sh

      - name: Run tests
        run: docker run --rm word-chatbot:sveltekit pytest tests/

      - name: Push to registry
        run: |
          docker tag word-chatbot:sveltekit myregistry/word-chatbot:latest
          docker push myregistry/word-chatbot:latest
```

## Support

For issues or questions:
1. Check container logs: `docker logs word-chatbot-sveltekit`
2. Review this guide's troubleshooting section
3. Verify `.env` configuration matches `.env.example`
4. Ensure Docker and system dependencies are up to date
