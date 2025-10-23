#!/bin/bash
# ===========================================================================
# Docker Run Script for SvelteKit Single-Container Deployment
# ===========================================================================
# This script runs the pre-built Docker container with proper configuration
# ===========================================================================

set -e  # Exit on error

echo "=================================================="
echo "Running SvelteKit Single-Container"
echo "=================================================="
echo ""

# Configuration
CONTAINER_NAME="word-chatbot-sveltekit"
IMAGE_NAME="word-chatbot:sveltekit"
HOST_PORT="3004"
CONTAINER_PORT="8000"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found"
    echo "Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Please edit .env to add your API keys before starting"
        exit 1
    else
        echo "ERROR: .env.example not found"
        exit 1
    fi
fi

# Check if image exists
if ! docker images "word-chatbot:sveltekit" | grep -q "sveltekit"; then
    echo "ERROR: Docker image ${IMAGE_NAME} not found"
    echo "Please build it first with: ./scripts/build-docker.sh"
    exit 1
fi

# Stop and remove existing container if running
if docker ps -a | grep -q "${CONTAINER_NAME}"; then
    echo "Stopping and removing existing container..."
    docker stop "${CONTAINER_NAME}" 2>/dev/null || true
    docker rm "${CONTAINER_NAME}" 2>/dev/null || true
    echo ""
fi

echo "Starting container..."
echo "  Name: ${CONTAINER_NAME}"
echo "  Port: 127.0.0.1:${HOST_PORT} -> ${CONTAINER_PORT}"
echo "  Image: ${IMAGE_NAME}"
echo ""

# Run container in detached mode
docker run -d \
  --name "${CONTAINER_NAME}" \
  -p "127.0.0.1:${HOST_PORT}:${CONTAINER_PORT}" \
  --env-file .env \
  --restart unless-stopped \
  "${IMAGE_NAME}"

# Wait a moment for container to start
sleep 2

echo ""
echo "=================================================="
echo "Container Started Successfully!"
echo "=================================================="
echo ""

# Show container status
echo "Container Status:"
docker ps | head -1
docker ps | grep "${CONTAINER_NAME}"
echo ""

echo "Access Points:"
echo "  Frontend: http://localhost:${HOST_PORT}/sageapp04/"
echo "  API Docs: http://localhost:${HOST_PORT}/docs"
echo "  Health Check: http://localhost:${HOST_PORT}/health"
echo ""

echo "Useful Commands:"
echo "  View logs:       docker logs -f ${CONTAINER_NAME}"
echo "  Stop container:  docker stop ${CONTAINER_NAME}"
echo "  Start container: docker start ${CONTAINER_NAME}"
echo "  Remove container: docker rm -f ${CONTAINER_NAME}"
echo ""

echo "Showing recent logs (Ctrl+C to exit)..."
echo "=================================================="
sleep 2
docker logs -f "${CONTAINER_NAME}"
