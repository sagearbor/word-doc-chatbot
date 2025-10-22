#!/bin/bash
# Word Doc Chatbot Startup Script
# Starts both backend and frontend services

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
BACKEND_PORT=8004
FRONTEND_PORT=3004
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Word Doc Chatbot - Startup Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if .env exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please create .env file from .env.example"
    exit 1
fi

# Check if ports are available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${RED}Error: Port $port is already in use!${NC}"
        lsof -Pi :$port -sTCP:LISTEN
        return 1
    fi
    return 0
}

echo "Checking ports..."
check_port $BACKEND_PORT || exit 1
check_port $FRONTEND_PORT || exit 1
echo -e "${GREEN}✓ Ports $BACKEND_PORT and $FRONTEND_PORT are available${NC}"
echo ""

# Start backend
echo -e "${BLUE}Starting backend on port $BACKEND_PORT...${NC}"
cd "$PROJECT_ROOT"
uvicorn backend.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT > /tmp/word-doc-backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
echo "  Log file: /tmp/word-doc-backend.log"
echo ""

# Wait a bit for backend to start
sleep 2

# Check if backend is healthy
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}Error: Backend failed to start!${NC}"
    echo "Check logs at /tmp/word-doc-backend.log"
    exit 1
fi

# Start frontend
echo -e "${BLUE}Starting frontend on port $FRONTEND_PORT...${NC}"
streamlit run frontend/streamlit_app.py --server.port $FRONTEND_PORT > /tmp/word-doc-frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
echo "  Log file: /tmp/word-doc-frontend.log"
echo ""

# Save PIDs for stop script
echo $BACKEND_PID > /tmp/word-doc-backend.pid
echo $FRONTEND_PID > /tmp/word-doc-frontend.pid

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Services started successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Backend:  ${BLUE}http://localhost:$BACKEND_PORT${NC}"
echo -e "Frontend: ${BLUE}http://localhost:$FRONTEND_PORT${NC}"
echo -e "API Docs: ${BLUE}http://localhost:$BACKEND_PORT/docs${NC}"
echo ""
echo "To view logs:"
echo "  Backend:  tail -f /tmp/word-doc-backend.log"
echo "  Frontend: tail -f /tmp/word-doc-frontend.log"
echo ""
echo "To stop services:"
echo "  ./stop.sh"
echo ""
echo -e "${BLUE}Press Ctrl+C to stop monitoring (services will continue running)${NC}"
echo ""

# Monitor both processes
tail -f /tmp/word-doc-backend.log /tmp/word-doc-frontend.log
