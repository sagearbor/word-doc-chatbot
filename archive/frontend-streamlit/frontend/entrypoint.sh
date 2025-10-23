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
