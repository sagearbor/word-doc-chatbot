# Docker Scripts Quick Reference

This directory contains helper scripts for managing the SvelteKit single-container Docker deployment.

## Available Scripts

### `build-docker.sh`
Build the multi-stage Docker image containing SvelteKit frontend and FastAPI backend.

```bash
# Build with default settings (BASE_URL_PATH=/sageapp04)
./scripts/build-docker.sh

# Build with custom BASE_URL_PATH
BASE_URL_PATH=/custom-path ./scripts/build-docker.sh

# Build with no path prefix (root deployment)
BASE_URL_PATH= ./scripts/build-docker.sh
```

**What it does:**
1. Validates Dockerfile and project structure exist
2. Builds Stage 1: SvelteKit frontend compilation
3. Builds Stage 2: Python backend + static files
4. Tags image as `word-chatbot:sveltekit` and `word-chatbot:latest`
5. Shows resulting Docker images

**When to run:**
- First time setup
- After frontend code changes
- After backend code changes
- After dependency updates
- To change BASE_URL_PATH

---

### `run-docker.sh`
Start the Docker container with proper configuration.

```bash
./scripts/run-docker.sh
```

**What it does:**
1. Checks if `.env` file exists
2. Validates Docker image is built
3. Stops/removes any existing container
4. Starts new container in detached mode
5. Maps port 127.0.0.1:3004 → container:8000
6. Loads environment variables from `.env`
7. Enables auto-restart policy
8. Shows container status and logs

**Container configuration:**
- Name: `word-chatbot-sveltekit`
- Port: `127.0.0.1:3004:8000`
- Restart: `unless-stopped`
- Environment: From `.env` file

**When to run:**
- After building image
- To start stopped container
- After updating `.env` file

---

### `stop-docker.sh`
Stop the running Docker container gracefully.

```bash
./scripts/stop-docker.sh
```

**What it does:**
1. Checks if container is running
2. Stops container gracefully (SIGTERM)
3. Keeps container for potential restart

**After stopping:**
- Restart: `docker start word-chatbot-sveltekit`
- Remove: `docker rm word-chatbot-sveltekit`
- Fresh start: `./scripts/run-docker.sh`

---

## Common Workflows

### First Time Setup

```bash
# 1. Configure environment
cp .env.example .env
nano .env  # Add API keys

# 2. Build image
./scripts/build-docker.sh

# 3. Start container
./scripts/run-docker.sh

# 4. Verify deployment
curl http://localhost:3004/health
# Open http://localhost:3004/sageapp04/ in browser
```

### Update Frontend Code

```bash
# 1. Make changes to frontend-new/src/

# 2. Rebuild image (includes frontend build)
./scripts/build-docker.sh

# 3. Restart container
docker stop word-chatbot-sveltekit
docker rm word-chatbot-sveltekit
./scripts/run-docker.sh
```

### Update Backend Code

```bash
# 1. Make changes to backend/

# 2. Rebuild image
./scripts/build-docker.sh

# 3. Restart container
docker stop word-chatbot-sveltekit
docker rm word-chatbot-sveltekit
./scripts/run-docker.sh
```

### Update Environment Variables

```bash
# 1. Edit .env file
nano .env

# 2. Restart container (rebuilding not needed)
docker stop word-chatbot-sveltekit
docker rm word-chatbot-sveltekit
./scripts/run-docker.sh
```

### Change BASE_URL_PATH

```bash
# 1. Rebuild with new path
BASE_URL_PATH=/new-path ./scripts/build-docker.sh

# 2. Update .env
nano .env  # Set BASE_URL_PATH=/new-path

# 3. Restart container
docker stop word-chatbot-sveltekit
docker rm word-chatbot-sveltekit
./scripts/run-docker.sh

# 4. Update NGINX config to match new path
```

### View Logs

```bash
# Real-time logs
docker logs -f word-chatbot-sveltekit

# Last 100 lines
docker logs --tail 100 word-chatbot-sveltekit

# With timestamps
docker logs -t word-chatbot-sveltekit

# Search logs for errors
docker logs word-chatbot-sveltekit 2>&1 | grep ERROR
```

### Troubleshooting

```bash
# Check container status
docker ps -a | grep word-chatbot

# Inspect container details
docker inspect word-chatbot-sveltekit

# Check resource usage
docker stats word-chatbot-sveltekit

# Execute command inside container
docker exec -it word-chatbot-sveltekit /bin/bash

# Verify static files
docker exec word-chatbot-sveltekit ls -la /app/static

# Check environment variables
docker exec word-chatbot-sveltekit env | grep AI_PROVIDER

# Test health endpoint
curl http://localhost:3004/health

# Test API docs
curl http://localhost:3004/docs
```

### Clean Rebuild

```bash
# Remove everything and start fresh
docker stop word-chatbot-sveltekit
docker rm word-chatbot-sveltekit
docker rmi word-chatbot:sveltekit word-chatbot:latest

# Clear Docker build cache (optional)
docker builder prune

# Rebuild from scratch
./scripts/build-docker.sh
./scripts/run-docker.sh
```

## Script Exit Codes

All scripts use `set -e` and will exit with non-zero code on errors:

- **0**: Success
- **1**: Configuration error (missing files, invalid setup)
- **Non-zero**: Command execution failure

## Environment Variables

### Build-Time Variables

Used during `build-docker.sh`:

```bash
BASE_URL_PATH=/sageapp04  # Path prefix for reverse proxy
```

### Runtime Variables

Required in `.env` file for `run-docker.sh`:

```bash
# AI Provider (required)
AI_PROVIDER=azure_openai
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEFAULT_DEPLOYMENT_NAME=gpt-4o-mini

# Application Settings (optional)
ENVIRONMENT=production
DEBUG_MODE=false
APP_TITLE=Word Document Chatbot
MAX_FILE_SIZE_MB=10
```

## Manual Docker Commands

If you prefer to run Docker commands manually:

```bash
# Build
docker build \
  --file Dockerfile.sveltekit \
  --build-arg BASE_URL_PATH=/sageapp04 \
  --tag word-chatbot:sveltekit \
  .

# Run
docker run -d \
  --name word-chatbot-sveltekit \
  -p 127.0.0.1:3004:8000 \
  --env-file .env \
  --restart unless-stopped \
  word-chatbot:sveltekit

# Stop
docker stop word-chatbot-sveltekit

# Remove
docker rm word-chatbot-sveltekit

# Logs
docker logs -f word-chatbot-sveltekit
```

## Additional Resources

- **Full Documentation**: `/dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot/DOCKER_SVELTEKIT.md`
- **NGINX Setup**: `/dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot/NGINX_DEPLOYMENT_GUIDE.md`
- **Project Guide**: `/dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot/CLAUDE.md`
- **Docker Compose**: `/dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot/docker-compose.yml`
