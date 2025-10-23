# SvelteKit Single-Container Deployment - Summary

## Files Created

### Core Docker Files

1. **`/dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot/Dockerfile.sveltekit`**
   - Multi-stage Dockerfile for building and deploying the application
   - Stage 1: Builds SvelteKit frontend as static site (Node.js 18 Alpine)
   - Stage 2: Python 3.11 slim container serving backend + static files
   - Security: Non-root user (appuser), health checks, minimal image size
   - Configurable BASE_URL_PATH via build args

2. **`/dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot/.dockerignore`** (updated)
   - Excludes unnecessary files from Docker build context
   - Added Node.js patterns (node_modules, .svelte-kit, build artifacts)
   - Added test files and archive directories
   - Reduces build context size and build time

### Build and Run Scripts

3. **`/dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot/scripts/build-docker.sh`** (executable)
   - Automated Docker image build script
   - Validates project structure before building
   - Configurable BASE_URL_PATH via environment variable
   - Tags images as `word-chatbot:sveltekit` and `word-chatbot:latest`
   - Shows build progress and final image details

4. **`/dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot/scripts/run-docker.sh`** (executable)
   - Automated container start script
   - Validates .env file and Docker image exist
   - Stops/removes existing container if present
   - Starts container with proper port mapping (127.0.0.1:3004:8000)
   - Auto-restart policy: unless-stopped
   - Follows logs after start

5. **`/dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot/scripts/stop-docker.sh`** (executable)
   - Graceful container stop script
   - Provides instructions for restart or removal

### Documentation

6. **`/dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot/DOCKER_SVELTEKIT.md`**
   - Comprehensive deployment guide (11KB)
   - Architecture overview
   - Quick start instructions
   - NGINX reverse proxy configuration
   - Environment variable reference
   - Troubleshooting section
   - Security and performance optimization

7. **`/dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot/scripts/README.md`**
   - Quick reference for Docker scripts
   - Common workflows (first setup, updates, troubleshooting)
   - Manual Docker commands
   - Environment variable documentation

### Configuration

8. **`/dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot/.env.example`** (updated)
   - Added SvelteKit deployment section
   - Documented BASE_URL_PATH configuration
   - Added NGINX reverse proxy examples
   - Production settings template

## How to Use

### First Time Setup (3 Steps)

```bash
# 1. Navigate to project root
cd /dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot

# 2. Configure environment
cp .env.example .env
nano .env  # Add your API keys (AI_PROVIDER, AZURE_OPENAI_API_KEY, etc.)

# 3. Build and run
./scripts/build-docker.sh
./scripts/run-docker.sh
```

### Access Application

Once running, access:
- **Frontend UI**: http://localhost:3004/sageapp04/
- **API Documentation**: http://localhost:3004/docs
- **Health Check**: http://localhost:3004/health

### Common Commands

```bash
# View logs
docker logs -f word-chatbot-sveltekit

# Stop container
./scripts/stop-docker.sh

# Restart container
docker start word-chatbot-sveltekit

# Rebuild after code changes
./scripts/build-docker.sh
docker stop word-chatbot-sveltekit && docker rm word-chatbot-sveltekit
./scripts/run-docker.sh
```

## Architecture Details

### Container Structure

```
word-chatbot:sveltekit (Final Image)
├── /app/backend/          # FastAPI backend code
├── /app/static/           # Built SvelteKit static files
├── /app/requirements.txt  # Python dependencies
└── User: appuser (UID 1000)
```

### Port Mapping

- **Container Internal**: Port 8000 (FastAPI)
- **Host**: 127.0.0.1:3004 (accessible only from localhost)
- **NGINX Proxy**: Forwards external traffic to localhost:3004

### URL Structure

When deployed with BASE_URL_PATH=/sageapp04:

```
External Request → NGINX → http://127.0.0.1:3004/sageapp04/
                              ↓
                    FastAPI Container (Port 8000)
                              ↓
                    ├─ /sageapp04/* → Static files (SvelteKit)
                    └─ /docs, /health, etc. → API endpoints
```

## Configuration Options

### Build-Time Configuration

Set before building Docker image:

```bash
# Default: /sageapp04
BASE_URL_PATH=/sageapp04 ./scripts/build-docker.sh

# Custom path
BASE_URL_PATH=/my-app ./scripts/build-docker.sh

# Root deployment (no prefix)
BASE_URL_PATH= ./scripts/build-docker.sh
```

**Note**: Changing BASE_URL_PATH requires rebuilding the Docker image.

### Runtime Configuration

Set in `.env` file before running container:

```bash
# Required
AI_PROVIDER=azure_openai
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEFAULT_DEPLOYMENT_NAME=gpt-4o-mini

# Optional
ENVIRONMENT=production
DEBUG_MODE=false
MAX_FILE_SIZE_MB=10
```

**Note**: Changing .env requires restarting the container (not rebuilding).

## NGINX Reverse Proxy Setup

### Recommended Configuration (Without Trailing Slash)

Add to your NGINX configuration:

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

Then reload NGINX:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Security Features

### Built-In Security

1. **Non-Root User**: Container runs as appuser (UID 1000)
2. **Localhost Binding**: Port bound to 127.0.0.1 only
3. **Health Checks**: Automatic container health monitoring
4. **Minimal Image**: Based on python:3.11-slim
5. **No Secrets in Image**: API keys loaded from .env at runtime

### Production Hardening

For production deployments, consider:

- Enable HTTPS in NGINX with SSL certificates
- Implement rate limiting in NGINX
- Use Docker secrets instead of .env files
- Enable read-only filesystem: `--read-only --tmpfs /tmp`
- Drop all capabilities: `--cap-drop ALL`
- Regular security updates

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs word-chatbot-sveltekit

# Common issues:
# 1. Missing .env file → cp .env.example .env
# 2. Invalid API keys → verify in .env
# 3. Port conflict → change HOST_PORT in run-docker.sh
```

### Frontend 404 Error

```bash
# Verify static files
docker exec word-chatbot-sveltekit ls -la /app/static

# Check URL (must include path prefix)
# Correct: http://localhost:3004/sageapp04/
# Wrong: http://localhost:3004/
```

### API Calls Failing

```bash
# Test health endpoint
curl http://localhost:3004/health

# Check environment variables
docker exec word-chatbot-sveltekit env | grep AI_PROVIDER

# View backend logs
docker logs word-chatbot-sveltekit | grep ERROR
```

## Performance Considerations

### Image Size

- Stage 1 (frontend-builder): ~500MB (discarded after build)
- Stage 2 (final image): ~400-500MB
- Multi-stage design minimizes final image size

### Build Time

- First build: 3-5 minutes (downloads dependencies)
- Subsequent builds: 1-2 minutes (uses Docker cache)
- Frontend changes only: 1-2 minutes (rebuilds both stages)
- Backend changes only: 1-2 minutes (rebuilds both stages)

### Runtime Resources

Recommended minimum:
- CPU: 1 core
- Memory: 1GB
- Disk: 1GB

Production recommended:
- CPU: 2 cores
- Memory: 2GB
- Disk: 2GB

## Next Steps

1. **Initial Deployment**:
   - Configure .env with API keys
   - Run `./scripts/build-docker.sh`
   - Run `./scripts/run-docker.sh`
   - Test at http://localhost:3004/sageapp04/

2. **NGINX Setup** (if deploying behind reverse proxy):
   - Add location block to NGINX config
   - Reload NGINX
   - Test external access

3. **Production Hardening**:
   - Enable HTTPS in NGINX
   - Implement rate limiting
   - Set up monitoring and logging
   - Configure backups

4. **Maintenance**:
   - Monitor logs: `docker logs -f word-chatbot-sveltekit`
   - Update dependencies regularly
   - Test changes in development first

## Additional Resources

- **Full Documentation**: `DOCKER_SVELTEKIT.md`
- **Script Reference**: `scripts/README.md`
- **Project Guide**: `CLAUDE.md`
- **NGINX Guide**: `NGINX_DEPLOYMENT_GUIDE.md`
- **Docker Compose**: `docker-compose.yml` (multi-container alternative)

## Summary

You now have a complete single-container Docker deployment solution for the SvelteKit + FastAPI application with:

- ✅ Multi-stage Dockerfile optimized for production
- ✅ Automated build and run scripts
- ✅ Comprehensive documentation
- ✅ Security best practices (non-root user, health checks)
- ✅ NGINX reverse proxy support
- ✅ Easy configuration via environment variables

The deployment is production-ready and follows Docker and security best practices.
