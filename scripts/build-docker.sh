#!/bin/bash
# ===========================================================================
# Docker Build Script for SvelteKit Single-Container Deployment
# ===========================================================================
# This script builds a multi-stage Docker image containing:
#   - SvelteKit frontend (built as static site)
#   - FastAPI backend (serving both API and static files)
# ===========================================================================

set -e  # Exit on error

echo "=================================================="
echo "Building SvelteKit Single-Container Docker Image"
echo "=================================================="
echo ""

# Configuration
IMAGE_NAME="word-chatbot"
TAG_SVELTEKIT="sveltekit"
TAG_LATEST="latest"
BASE_URL_PATH="${BASE_URL_PATH:-/sageapp04}"

echo "Configuration:"
echo "  Image Name: ${IMAGE_NAME}"
echo "  Tags: ${TAG_SVELTEKIT}, ${TAG_LATEST}"
echo "  Base URL Path: ${BASE_URL_PATH}"
echo ""

# Check if Dockerfile exists
if [ ! -f "Dockerfile.sveltekit" ]; then
    echo "ERROR: Dockerfile.sveltekit not found in current directory"
    echo "Please run this script from the project root"
    exit 1
fi

# Check if frontend-new exists
if [ ! -d "frontend-new" ]; then
    echo "ERROR: frontend-new directory not found"
    echo "Please ensure the SvelteKit frontend is in frontend-new/"
    exit 1
fi

# Check if backend exists
if [ ! -d "backend" ]; then
    echo "ERROR: backend directory not found"
    echo "Please ensure the FastAPI backend is in backend/"
    exit 1
fi

echo "Building Docker image..."
echo ""

# Build with progress output
docker build \
  --file Dockerfile.sveltekit \
  --build-arg BASE_URL_PATH="${BASE_URL_PATH}" \
  --tag "${IMAGE_NAME}:${TAG_SVELTEKIT}" \
  --tag "${IMAGE_NAME}:${TAG_LATEST}" \
  --progress=plain \
  .

echo ""
echo "=================================================="
echo "Build Complete!"
echo "=================================================="
echo ""
echo "Docker images created:"
docker images | head -1
docker images | grep "${IMAGE_NAME}"
echo ""
echo "To run the container:"
echo "  ./scripts/run-docker.sh"
echo ""
echo "Or manually:"
echo "  docker run -d --name word-chatbot-sveltekit \\"
echo "    -p 127.0.0.1:3004:8000 \\"
echo "    --env-file .env \\"
echo "    ${IMAGE_NAME}:${TAG_SVELTEKIT}"
echo ""
