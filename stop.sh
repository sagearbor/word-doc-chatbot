#!/bin/bash
# Word Doc Chatbot Stop Script
# Stops both backend and frontend services

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Stopping Word Doc Chatbot Services${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Stop backend
if [ -f /tmp/word-doc-backend.pid ]; then
    BACKEND_PID=$(cat /tmp/word-doc-backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        echo -e "${GREEN}✓ Backend stopped${NC}"
    else
        echo -e "${RED}Backend process not running${NC}"
    fi
    rm -f /tmp/word-doc-backend.pid
else
    echo "No backend PID file found, trying pkill..."
    pkill -f "uvicorn backend.main:app" && echo -e "${GREEN}✓ Backend stopped${NC}" || echo "No backend process found"
fi

# Stop frontend
if [ -f /tmp/word-doc-frontend.pid ]; then
    FRONTEND_PID=$(cat /tmp/word-doc-frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        echo -e "${GREEN}✓ Frontend stopped${NC}"
    else
        echo -e "${RED}Frontend process not running${NC}"
    fi
    rm -f /tmp/word-doc-frontend.pid
else
    echo "No frontend PID file found, trying pkill..."
    pkill -f "streamlit run frontend/streamlit_app.py" && echo -e "${GREEN}✓ Frontend stopped${NC}" || echo "No frontend process found"
fi

echo ""
echo -e "${GREEN}All services stopped${NC}"
