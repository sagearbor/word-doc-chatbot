# NGINX Deployment Guide

> **IMPORTANT: SIMPLIFIED WITH SVELTEKIT!**
> This application has been migrated from Streamlit to SvelteKit. The nginx-helper container is **NO LONGER NEEDED**.
> SvelteKit's adapter-static handles base paths natively at build time, eliminating the need for path manipulation middleware.
>
> **Migration benefits:**
> - Single Docker container (backend + frontend)
> - No nginx-helper required
> - Simpler architecture and easier maintenance
> - Native base path support in SvelteKit
>
> See `SVELTEKIT_MIGRATION.md` for migration details.

---

This guide explains how to deploy the SvelteKit application behind NGINX reverse proxy with path prefixes (e.g., `/sageapp04/`). The setup is significantly simpler than the previous Streamlit-based deployment.

## Table of Contents
- [Problem Overview](#problem-overview)
- [Solution Architecture](#solution-architecture)
- [Step-by-Step Setup](#step-by-step-setup)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Deployment Scenarios](#deployment-scenarios)

---

## Problem Overview

### The Challenge

When deploying Streamlit apps behind NGINX with path prefixes, you'll encounter WebSocket connection failures if not configured correctly.

**Main NGINX Configuration (Managed by IT):**
```nginx
location = /sageapp04  { return 301 /sageapp04/; }
location /sageapp04/  { proxy_pass http://127.0.0.1:3004/; }  # Trailing slash strips prefix
```

**What happens:**
1. Browser requests: `https://aidemo.dcri.duke.edu/sageapp04/`
2. NGINX strips `/sageapp04/` and proxies to: `http://127.0.0.1:3004/` (root path)
3. Without proper configuration, Streamlit generates incorrect WebSocket URLs
4. **Result:** WebSocket connection fails, app appears frozen

### Why Streamlit Is Special

Streamlit uses WebSockets for real-time communication. When served at a path prefix:
- Streamlit needs to know the external path (`/sageapp04/`) to generate correct WebSocket URLs
- But NGINX strips this prefix before forwarding requests
- We need a "helper" layer to re-add the prefix

---

## Solution Architecture

### SvelteKit Deployment (Current - Simplified)

With SvelteKit, the architecture is dramatically simplified:

```
Browser: https://aidemo.dcri.duke.edu/sageapp04/
   ↓
Main NGINX: Proxies to 127.0.0.1:8000 (with or without path stripping)
   ↓
FastAPI + SvelteKit (single container, port 8000):
  - FastAPI backend serves API at /api/*
  - FastAPI serves SvelteKit static files with correct base path
  - SvelteKit built with base: '/sageapp04' (handles paths automatically)
```

**Key components:**
1. **Main NGINX** (managed by IT) - Reverse proxy only
2. **Single Docker container** - FastAPI serves both API and static frontend

**Benefits:**
- No nginx-helper container needed
- No path manipulation middleware required
- SvelteKit handles base paths at build time
- Single container deployment
- Simpler configuration and troubleshooting

### Legacy Streamlit Deployment (Deprecated)

<details>
<summary>Click to expand legacy Streamlit architecture (for reference only)</summary>

We used a lightweight NGINX helper container to fix the path mismatch:

```
Browser: https://aidemo.dcri.duke.edu/sageapp04/
   ↓
Main NGINX: Strips /sageapp04/ → proxies to 127.0.0.1:3004/
   ↓
NGINX Helper (port 3004): Adds /sageapp04/ back → proxies to 127.0.0.1:8501/sageapp04/
   ↓
Streamlit (port 8501): Configured with --server.baseUrlPath=/sageapp04 → serves correctly
```

**Key components:**
1. **Main NGINX** (managed by IT) - Strips path prefix
2. **NGINX Helper** (your control) - Restores path prefix
3. **Streamlit app** (your app) - Configured with base URL path

</details>

---

## Step-by-Step Setup (SvelteKit)

### 1. Build the SvelteKit Application

SvelteKit needs to be built with the correct base path:

```bash
# Set base path for the build
cd frontend-new
BASE_URL_PATH=/sageapp04 npm run build

# This creates frontend-new/build/ with static files
```

The base path is configured in `svelte.config.js` and read from the `BASE_URL_PATH` environment variable.

### 2. Build the Docker Container

```bash
# From project root
docker build -f Dockerfile.sveltekit -t word-chatbot:sveltekit .

# Run the container
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name word-chatbot \
  word-chatbot:sveltekit
```

The Dockerfile automatically:
- Installs Node.js dependencies
- Builds SvelteKit with correct base path from environment
- Sets up FastAPI to serve both API and static files
- Configures all paths correctly

### 3. Configure NGINX (IT-Managed)

The main NGINX configuration is simple - just proxy to the application:

```nginx
# Option 1: Without path stripping (recommended)
location /sageapp04 {
    proxy_pass http://127.0.0.1:8000;

    # WebSocket support (if needed in future)
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";

    # Standard reverse proxy headers
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Timeouts
    proxy_read_timeout 86400;
    proxy_buffering off;
}

# Option 2: With path stripping (also works)
location /sageapp04/ {
    proxy_pass http://127.0.0.1:8000/;  # Trailing slash strips /sageapp04

    # Same headers as above...
}
```

**Note:** Both options work with SvelteKit! The application handles paths correctly either way.

### 4. Set Environment Variables

Create or update `.env` in project root:

```bash
# AI Provider Configuration
CURRENT_AI_PROVIDER=azure_openai
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEFAULT_DEPLOYMENT_NAME=gpt-5-mini

# Base path for reverse proxy deployment
BASE_URL_PATH=/sageapp04

# Backend URL for API calls (used by SvelteKit at build time)
PUBLIC_BACKEND_URL=http://localhost:8000
```

---

## Legacy Streamlit Setup (Deprecated)

<details>
<summary>Click to expand legacy Streamlit setup instructions (for reference only)</summary>

### 1. Create `.streamlit/config.toml`

Create `frontend/.streamlit/config.toml`:

```toml
[server]
# Enable CORS for reverse proxy
enableCORS = false
enableXsrfProtection = false

# WebSocket compression can cause issues with some reverse proxies
enableWebsocketCompression = false

# The base URL path will be set dynamically via the entrypoint script
# This file provides default configuration; baseUrlPath is set via CLI
```

### 2. Create `entrypoint.sh`

Create `frontend/entrypoint.sh`:

```bash
#!/bin/bash
# Entrypoint script for Streamlit app with configurable base URL path

set -e

# Default values
PORT=${STREAMLIT_PORT:-8501}
BASE_URL_PATH=${BASE_URL_PATH:-}
SERVER_ADDRESS=${SERVER_ADDRESS:-0.0.0.0}

echo "=========================================="
echo "Starting Streamlit Application"
echo "=========================================="
echo "Port: $PORT"
echo "Base URL Path: ${BASE_URL_PATH:-'/' (root)}"
echo "Server Address: $SERVER_ADDRESS"
echo "=========================================="

# Build streamlit command
STREAMLIT_CMD="streamlit run frontend/streamlit_app.py"
STREAMLIT_CMD="$STREAMLIT_CMD --server.port=$PORT"
STREAMLIT_CMD="$STREAMLIT_CMD --server.address=$SERVER_ADDRESS"
STREAMLIT_CMD="$STREAMLIT_CMD --server.enableCORS=false"
STREAMLIT_CMD="$STREAMLIT_CMD --server.enableXsrfProtection=false"
STREAMLIT_CMD="$STREAMLIT_CMD --server.enableWebsocketCompression=false"

# Add base URL path if specified
if [ -n "$BASE_URL_PATH" ]; then
    echo "Configuring base URL path: $BASE_URL_PATH"
    STREAMLIT_CMD="$STREAMLIT_CMD --server.baseUrlPath=$BASE_URL_PATH"
fi

echo "Executing: $STREAMLIT_CMD"
echo "=========================================="

# Execute streamlit
exec $STREAMLIT_CMD
```

Make it executable:
```bash
chmod +x frontend/entrypoint.sh
```

### 3. Create `nginx-helper.conf`

Create `nginx-helper.conf` in your project root:

```nginx
# NGINX Helper Configuration
# This helper sits between the main NGINX and the Streamlit application.

server {
    listen 80;
    server_name _;

    # Receive requests at root path (from main NGINX after it strips /sageapp04)
    location / {
        # Add /sageapp04 prefix back before proxying to Streamlit
        rewrite ^/(.*)$ /sageapp04/$1 break;

        # Proxy to Streamlit application
        # Adjust proxy_pass based on your deployment:
        # - Standalone: proxy_pass http://127.0.0.1:8501;
        # - Docker: proxy_pass http://streamlit-container:8501;
        proxy_pass http://127.0.0.1:8501;

        # WebSocket support (required for Streamlit)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Standard reverse proxy headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Streamlit-specific settings
        proxy_buffering off;
        proxy_read_timeout 86400;  # 24 hours for long-running operations
    }

    # Health check endpoint (optional)
    location /health {
        access_log off;
        return 200 "OK\n";
        add_header Content-Type text/plain;
    }
}
```

**Important:** Change the `rewrite` rule if using a different path:
- For `/sageapp04/`: `rewrite ^/(.*)$ /sageapp04/$1 break;`
- For `/myapp/`: `rewrite ^/(.*)$ /myapp/$1 break;`

### 4. Update Environment Configuration

Add to your `.env` file (or `.env.example`):

```bash
# NGINX / Reverse Proxy Configuration
# Set BASE_URL_PATH when deploying behind a reverse proxy with a path prefix
# Examples:
#   - For root deployment (https://mydomain.com/): leave empty
#   - For path deployment (https://mydomain.com/sageapp04/): /sageapp04
BASE_URL_PATH=/sageapp04

# Backend URL (adjust based on your deployment)
BACKEND_URL=http://127.0.0.1:8004

# Streamlit server settings
STREAMLIT_PORT=8501
SERVER_ADDRESS=0.0.0.0
```

---

</details>

## Testing (SvelteKit)

### 1. Test Application Locally

First, verify the application works standalone:

```bash
# Start the Docker container
docker run -d -p 8000:8000 --env-file .env --name word-chatbot word-chatbot:sveltekit

# Check health
curl http://localhost:8000/health
# Should return: {"status":"healthy"}

# Access the application
open http://localhost:8000
# Or if using base path:
open http://localhost:8000/sageapp04
```

**Expected:** Application loads correctly, can upload files and process documents

### 2. Test with NGINX Proxy

Set up local NGINX to test the reverse proxy configuration:

```bash
# Install NGINX (if not already installed)
# Ubuntu/Debian: sudo apt-get install nginx
# macOS: brew install nginx

# Create test config
sudo tee /etc/nginx/sites-available/word-chatbot-test <<EOF
server {
    listen 80;
    server_name localhost;

    location /sageapp04 {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
        proxy_read_timeout 86400;
    }
}
EOF

# Enable the config
sudo ln -s /etc/nginx/sites-available/word-chatbot-test /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Test
open http://localhost/sageapp04
```

**Expected:** Application loads correctly through NGINX proxy

### 3. Test Static Assets

Verify static assets (CSS, JS) load correctly:

```bash
# Check bundle loads
curl -I http://localhost:8000/sageapp04/_app/immutable/entry/start.*.js
# Should return: 200 OK

# Check CSS loads
curl -I http://localhost:8000/sageapp04/_app/immutable/assets/*.css
# Should return: 200 OK
```

### 4. Browser DevTools Check

Open browser DevTools (F12) → Network tab:
- All assets should return 200 OK
- No 404 errors for CSS/JS files
- Base paths should be correct in loaded URLs
- Console should have no errors

---

## Legacy Streamlit Testing (Deprecated)

<details>
<summary>Click to expand legacy Streamlit testing instructions (for reference only)</summary>

### 1. Test Streamlit Standalone (Without NGINX Helper)

First, verify Streamlit works with base path configuration:

```bash
# Set environment variable
export BASE_URL_PATH=/sageapp04

# Run using entrypoint script
./frontend/entrypoint.sh
```

Access: `http://localhost:8501/sageapp04/`

**Expected:** Streamlit UI loads correctly at the path prefix

### 2. Test with NGINX Helper

Start NGINX helper locally:

```bash
# In one terminal: Start Streamlit with base path
export BASE_URL_PATH=/sageapp04
./frontend/entrypoint.sh

# In another terminal: Start NGINX helper
# First, update nginx-helper.conf to use 127.0.0.1:8501
nginx -c $(pwd)/nginx-helper.conf -p $(pwd)
```

**Or using Docker:**
```bash
docker run -d \
  --name nginx-helper \
  -p 3004:80 \
  -v $(pwd)/nginx-helper.conf:/etc/nginx/conf.d/default.conf:ro \
  nginx:alpine
```

Access: `http://localhost:3004/` (note: NO path prefix in URL)

**Expected:** Streamlit UI loads correctly, WebSockets work

### 3. Test Health Check

```bash
curl http://localhost:3004/_stcore/health
# Should return: ok

curl http://localhost:3004/health
# Should return: OK
```

### 4. Browser Console Check

Open browser DevTools (F12) → Console tab
- **No WebSocket errors**: ✅ Working correctly
- **WebSocket connection failed**: ❌ Configuration issue

</details>

---

## Troubleshooting (SvelteKit)

### Issue: 404 Not Found

**Symptoms:**
- Accessing the app returns 404
- Static assets not loading

**Solutions:**
1. Verify BASE_URL_PATH is set correctly in .env
2. Rebuild Docker image with correct base path: `docker build -f Dockerfile.sveltekit -t word-chatbot:sveltekit .`
3. Check NGINX is proxying to correct port (8000)
4. Verify container is running: `docker ps | grep word-chatbot`
5. Check container logs: `docker logs word-chatbot`

### Issue: CSS/JS Not Loading

**Symptoms:**
- App loads but has no styling
- Browser console shows 404 errors for static assets

**Solutions:**
1. Verify SvelteKit was built with correct BASE_URL_PATH
2. Check browser Network tab - assets should load from correct base path
3. Rebuild frontend: `cd frontend-new && BASE_URL_PATH=/sageapp04 npm run build`
4. Rebuild Docker image
5. Ensure base path doesn't have trailing slash

### Issue: API Calls Failing

**Symptoms:**
- App loads but file uploads fail
- Document processing doesn't work

**Solutions:**
1. Check PUBLIC_BACKEND_URL in frontend-new/.env
2. Verify FastAPI is running: `curl http://localhost:8000/health`
3. Check CORS configuration in backend/main.py
4. Verify API endpoints are accessible: `curl http://localhost:8000/docs`
5. Check container logs for backend errors

### Issue: Container Won't Start

**Symptoms:**
- Docker container exits immediately
- `docker ps` doesn't show the container

**Solutions:**
1. Check logs: `docker logs word-chatbot`
2. Verify .env file exists and has required variables
3. Check for port conflicts: `lsof -i :8000`
4. Verify Docker image built successfully
5. Try running interactively: `docker run -it --env-file .env word-chatbot:sveltekit`

---

## Deployment Scenarios (SvelteKit)

### Scenario 1: POC/Demo (Path Prefix - e.g., /sageapp04/)

**Use case:** Multiple apps on shared domain: `https://demo.com/app1/`, `https://demo.com/app2/`

**Configuration:**
```bash
# .env
BASE_URL_PATH=/sageapp04
CURRENT_AI_PROVIDER=azure_openai
AZURE_OPENAI_API_KEY=your-key
PUBLIC_BACKEND_URL=http://localhost:8000

# Build and run
docker build -f Dockerfile.sveltekit -t word-chatbot:sveltekit .
docker run -d -p 8000:8000 --env-file .env --name word-chatbot word-chatbot:sveltekit
```

**Main NGINX config (managed by IT):**
```nginx
location = /sageapp04  { return 301 /sageapp04/; }
location /sageapp04 {
    proxy_pass http://127.0.0.1:8000;

    # Standard headers
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    proxy_buffering off;
    proxy_read_timeout 86400;
}
```

### Scenario 2: Production (Dedicated Domain - No Path Prefix)

**Use case:** App has its own domain: `https://myapp.company.com/`

**Configuration:**
```bash
# .env
BASE_URL_PATH=  # Empty - no path prefix
CURRENT_AI_PROVIDER=azure_openai
AZURE_OPENAI_API_KEY=your-key
PUBLIC_BACKEND_URL=http://localhost:8000

# Build and run
docker build -f Dockerfile.sveltekit -t word-chatbot:production .
docker run -d -p 8000:8000 --env-file .env --restart unless-stopped word-chatbot:production
```

**Main NGINX config:**
```nginx
server {
    listen 443 ssl;
    server_name myapp.company.com;

    location / {
        proxy_pass http://127.0.0.1:8000;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_buffering off;
        proxy_read_timeout 86400;
    }
}
```

### Scenario 3: Azure Container Instances

**Use case:** Cloud deployment on Azure

**Configuration:**
```bash
# Build and push to Azure Container Registry
az acr login --name yourregistry
docker tag word-chatbot:sveltekit yourregistry.azurecr.io/word-chatbot:latest
docker push yourregistry.azurecr.io/word-chatbot:latest

# Deploy to Azure Container Instances
az container create \
  --resource-group your-rg \
  --name word-chatbot \
  --image yourregistry.azurecr.io/word-chatbot:latest \
  --registry-login-server yourregistry.azurecr.io \
  --registry-username $(az acr credential show -n yourregistry --query username -o tsv) \
  --registry-password $(az acr credential show -n yourregistry --query passwords[0].value -o tsv) \
  --dns-name-label word-chatbot \
  --ports 8000 \
  --environment-variables \
    BASE_URL_PATH= \
    CURRENT_AI_PROVIDER=azure_openai \
    AZURE_OPENAI_API_KEY=your-key
```

---

## Legacy Streamlit Troubleshooting (Deprecated)

<details>
<summary>Click to expand legacy Streamlit troubleshooting (for reference only)</summary>

### Issue: WebSocket Connection Failed

**Symptoms:**
- App loads but appears frozen
- Browser console shows: `WebSocket connection to 'wss://...' failed`

**Solutions:**
1. Verify BASE_URL_PATH matches the NGINX rewrite rule
2. Check Streamlit logs for the actual baseUrlPath being used
3. Ensure NGINX helper is running and accessible
4. Verify WebSocket headers are set in nginx-helper.conf

### Issue: 404 Not Found

**Symptoms:**
- Accessing the app returns 404

**Solutions:**
1. Check that NGINX helper is running on the correct port
2. Verify main NGINX is proxying to the correct port
3. Check NGINX helper logs: `docker logs nginx-helper`

### Issue: CSS/JS Not Loading

**Symptoms:**
- App loads but looks broken (no styling)

**Solutions:**
1. Verify the rewrite rule in nginx-helper.conf
2. Check browser Network tab for failed resource requests
3. Ensure baseUrlPath doesn't have a trailing slash

### Issue: Backend API Calls Failing

**Symptoms:**
- App loads but API requests fail

**Solutions:**
1. Check BACKEND_URL environment variable
2. Ensure backend is accessible from Streamlit container
3. Verify CORS settings if frontend and backend on different origins

---

## Deployment Scenarios

### Scenario 1: POC/Demo (Path Prefix - e.g., /sageapp04/)

**Use case:** Multiple apps on shared domain: `https://demo.com/app1/`, `https://demo.com/app2/`

**Configuration:**
```bash
# .env
BASE_URL_PATH=/sageapp04
BACKEND_URL=http://127.0.0.1:8004

# Start Streamlit
./frontend/entrypoint.sh

# Start NGINX helper on port 3004
docker run -d --name nginx-helper -p 127.0.0.1:3004:80 \
  -v $(pwd)/nginx-helper.conf:/etc/nginx/conf.d/default.conf:ro \
  nginx:alpine
```

**Main NGINX config (managed by IT):**
```nginx
location = /sageapp04  { return 301 /sageapp04/; }
location /sageapp04/  { proxy_pass http://127.0.0.1:3004/; }
```

### Scenario 2: Production (Dedicated Domain - No Path Prefix)

**Use case:** App has its own domain: `https://myapp.company.com/`

**Configuration:**
```bash
# .env
BASE_URL_PATH=  # Empty - no path prefix
BACKEND_URL=http://127.0.0.1:8004

# Start Streamlit directly (no NGINX helper needed)
./frontend/entrypoint.sh
```

**Main NGINX config:**
```nginx
server {
    listen 443 ssl;
    server_name myapp.company.com;

    location / {
        proxy_pass http://127.0.0.1:8501;

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

### Scenario 3: Azure Web App (With Managed NGINX)

**Use case:** Deploying to Azure App Service

**Configuration:**
```bash
# Azure App Service Application Settings
BASE_URL_PATH=/  # Or empty
BACKEND_URL=https://backend-app.azurewebsites.net
STREAMLIT_PORT=8000  # Azure expects port 8000
```

**Note:** Azure App Service provides its own NGINX, so no nginx-helper is needed. Set BASE_URL_PATH to `/` or leave empty.

---

## Quick Reference

### Files to Create
- `frontend/.streamlit/config.toml` - Streamlit server configuration
- `frontend/entrypoint.sh` - Dynamic startup script
- `nginx-helper.conf` - NGINX helper configuration
- `.env` - Environment variables (update existing)

### Environment Variables
- `BASE_URL_PATH` - URL path prefix (e.g., `/sageapp04` or empty for root)
- `BACKEND_URL` - Backend API URL
- `STREAMLIT_PORT` - Port for Streamlit server (default: 8501)
- `SERVER_ADDRESS` - Server bind address (default: 0.0.0.0)

### Key NGINX Settings
```nginx
# Main NGINX (IT-managed) - Strips prefix
location /sageapp04/  { proxy_pass http://127.0.0.1:3004/; }  # Note trailing slash

# NGINX Helper (your control) - Restores prefix
rewrite ^/(.*)$ /sageapp04/$1 break;
proxy_pass http://127.0.0.1:8501;
```

### Testing Commands
```bash
# Test Streamlit health
curl http://localhost:8501/_stcore/health

# Test NGINX helper health
curl http://localhost:3004/health

# View Streamlit logs
tail -f ~/.streamlit/streamlit.log

# View NGINX helper logs (Docker)
docker logs -f nginx-helper
```

---

## What If IT Removes the Trailing Slash?

### The Change

If IT modifies the main NGINX configuration from:
```nginx
location /sageapp04/  { proxy_pass http://127.0.0.1:3004/; }  # WITH trailing slash (strips prefix)
```

To:
```nginx
location /sageapp04  { proxy_pass http://127.0.0.1:3004; }  # NO trailing slash (keeps prefix)
```

### Required Changes

**✅ GOOD NEWS**: If IT changes NGINX to keep the prefix, you can **REMOVE the nginx-helper entirely**! This simplifies your setup significantly.

**Files to Update** (search for `TRAILING_SLASH_CHANGE` in code comments):

**1. `docker-compose.yml`** - Comment out or remove nginx-helper service:
```yaml
# NGINX helper not needed if main NGINX keeps path prefix
# nginx-helper:
#   image: nginx:alpine
#   ...
```

**2. `frontend/entrypoint.sh`** - No changes needed (already configured via BASE_URL_PATH)

**3. Environment Variables** - Set BASE_URL_PATH:
```bash
export BASE_URL_PATH=/sageapp04
```

**4. Main NGINX** (managed by IT) - Both should work:
```nginx
# Recommended: Keep path prefix (no trailing slash on proxy_pass)
location = /sageapp04  { return 301 /sageapp04/; }
location /sageapp04  {
    proxy_pass http://127.0.0.1:3004;  # No trailing slash = keeps /sageapp04

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
```

### Comparison Table

| Main NGINX Config | nginx-helper Needed? | Direct Streamlit Access | Complexity |
|-------------------|----------------------|------------------------|------------|
| `proxy_pass http://...:3004/;` (WITH slash) | ✅ Yes | Via helper on :3004 | Higher |
| `proxy_pass http://...:3004;` (NO slash) | ❌ No | Direct on :3004 | Lower |

### Quick Migration Guide

If IT changes to no-trailing-slash configuration:

```bash
# 1. Stop current deployment
docker-compose down

# 2. Update docker-compose.yml - comment out nginx-helper
# See TRAILING_SLASH_CHANGE comment in file

# 3. Expose frontend directly
# In docker-compose.yml, add to frontend service:
#   ports:
#     - "127.0.0.1:3004:8501"

# 4. Set environment variable
export BASE_URL_PATH=/sageapp04

# 5. Restart
docker-compose up -d backend frontend

# 6. Test
curl http://localhost:3004/_stcore/health
```

**Result**: Simpler architecture without nginx-helper!

</details>

---

## Quick Reference (SvelteKit)

### Environment Variables
- `BASE_URL_PATH` - URL path prefix (e.g., `/sageapp04` or empty for root)
- `PUBLIC_BACKEND_URL` - Backend API URL (e.g., `http://localhost:8000`)
- `CURRENT_AI_PROVIDER` - AI provider selection
- Provider-specific API keys and endpoints

### Key Commands
```bash
# Build Docker image
docker build -f Dockerfile.sveltekit -t word-chatbot:sveltekit .

# Run container
docker run -d -p 8000:8000 --env-file .env word-chatbot:sveltekit

# Check health
curl http://localhost:8000/health

# View logs
docker logs -f word-chatbot

# Stop container
docker stop word-chatbot
```

### NGINX Configuration
```nginx
# Simple reverse proxy - no path manipulation needed
location /sageapp04 {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_buffering off;
    proxy_read_timeout 86400;
}
```

---

## Additional Resources

- [SvelteKit Documentation](https://kit.svelte.dev/docs)
- [SvelteKit adapter-static](https://kit.svelte.dev/docs/adapter-static)
- [NGINX Reverse Proxy Documentation](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
- [FastAPI Serving Static Files](https://fastapi.tiangolo.com/tutorial/static-files/)
- [SVELTEKIT_MIGRATION.md](./SVELTEKIT_MIGRATION.md) - Migration details

---

## Summary

### SvelteKit Deployment (Current)

**For path-based deployment (POC/demo with /sageapp04):**
1. Set `BASE_URL_PATH=/sageapp04` in .env
2. Build Docker image (handles base path automatically)
3. Run single container on port 8000
4. Configure NGINX to proxy to container
5. No nginx-helper needed!

**For root deployment (production with dedicated domain):**
1. Set `BASE_URL_PATH=` (empty) in .env
2. Build and run Docker image
3. Configure NGINX to proxy to container
4. Single container, simple configuration

**Key advantage:** SvelteKit handles base paths natively at build time, eliminating the need for runtime path manipulation middleware.

### Legacy Streamlit Deployment (Deprecated)

See collapsed sections above for legacy Streamlit deployment information (for reference only).
