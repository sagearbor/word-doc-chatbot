# NGINX Deployment Guide for Streamlit Applications

This guide explains how to deploy Streamlit applications behind NGINX reverse proxy with path prefixes (e.g., `/sageapp04/`). This setup is required when hosting multiple applications on a single domain with different URL paths.

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

We use a lightweight NGINX helper container to fix the path mismatch:

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

---

## Step-by-Step Setup

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

## Testing

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

---

## Troubleshooting

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

---

## Additional Resources

- [Streamlit Documentation - Reverse Proxy](https://docs.streamlit.io/knowledge-base/deploy/deploy-streamlit-using-nginx)
- [NGINX Reverse Proxy Documentation](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
- [WebSocket Proxying with NGINX](https://nginx.org/en/docs/http/websocket.html)
- [NGINX proxy_pass Trailing Slash Behavior](http://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_pass)

---

## Summary

**For path-based deployment (recommended for POC/demo):**
1. ✅ Use NGINX helper container
2. ✅ Set BASE_URL_PATH environment variable
3. ✅ Use entrypoint.sh to start Streamlit with baseUrlPath

**For root deployment (recommended for production):**
1. ✅ Set BASE_URL_PATH to empty
2. ✅ No NGINX helper needed
3. ✅ Direct NGINX → Streamlit proxy

**Remember:** The key is ensuring Streamlit's baseUrlPath matches the external URL path that users see in their browser.
