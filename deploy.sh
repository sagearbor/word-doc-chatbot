#!/bin/bash
# Quick Docker rebuild and deploy script for Word Doc Chatbot

set -e  # Exit on error

# Configuration
IMAGE_NAME="word-chatbot"
TAG="v0.3"
CONTAINER_NAME="word-chatbot"
PORT="3004"

echo "=========================================="
echo "Word Doc Chatbot - Docker Deployment"
echo "=========================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please copy .env.example to .env and configure it."
    exit 1
fi

# Stop and remove existing container
echo "Step 1/4: Stopping and removing existing container..."
if docker ps -a | grep -q $CONTAINER_NAME; then
    docker stop $CONTAINER_NAME 2>/dev/null || true
    docker rm $CONTAINER_NAME 2>/dev/null || true
    echo "  ✓ Container removed"
else
    echo "  ✓ No existing container found"
fi

# Remove old image (optional, uncomment to force complete rebuild)
# echo "Removing old image..."
# docker rmi $IMAGE_NAME:$TAG 2>/dev/null || true

# Build new image (no cache)
echo ""
echo "Step 2/4: Building Docker image (no cache)..."
docker build --no-cache -f Dockerfile.sveltekit -t $IMAGE_NAME:$TAG .

# Run container
echo ""
echo "Step 3/4: Starting container on port $PORT..."
docker run -d \
  -p $PORT:8000 \
  --env-file .env \
  --name $CONTAINER_NAME \
  --restart unless-stopped \
  $IMAGE_NAME:$TAG

# Wait for container to start
echo ""
echo "Step 4/4: Verifying container status..."
sleep 2

if docker ps | grep -q $CONTAINER_NAME; then
    echo "  ✓ Container running successfully"
else
    echo "  ✗ Container failed to start. Check logs:"
    echo "    docker logs $CONTAINER_NAME"
    exit 1
fi

# Show status
echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Container:  $CONTAINER_NAME"
echo "Image:      $IMAGE_NAME:$TAG"
echo "Port:       $PORT"
echo ""
echo "Access application:"
echo "  Local:    http://localhost:$PORT"
echo "  Remote:   http://<your-server>:$PORT"
echo ""
echo "Useful commands:"
echo "  View logs:    docker logs -f $CONTAINER_NAME"
echo "  Stop:         docker stop $CONTAINER_NAME"
echo "  Start:        docker start $CONTAINER_NAME"
echo "  Restart:      docker restart $CONTAINER_NAME"
echo "  Remove:       docker stop $CONTAINER_NAME && docker rm $CONTAINER_NAME"
echo ""
