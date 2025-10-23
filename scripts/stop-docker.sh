#!/bin/bash
# ===========================================================================
# Docker Stop Script for SvelteKit Single-Container
# ===========================================================================

set -e

CONTAINER_NAME="word-chatbot-sveltekit"

echo "Stopping ${CONTAINER_NAME}..."

if docker ps | grep -q "${CONTAINER_NAME}"; then
    docker stop "${CONTAINER_NAME}"
    echo "Container stopped successfully"
else
    echo "Container is not running"
fi

echo ""
echo "To remove the container completely:"
echo "  docker rm ${CONTAINER_NAME}"
echo ""
echo "To start again:"
echo "  ./scripts/run-docker.sh"
