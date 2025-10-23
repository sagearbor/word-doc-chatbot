#!/bin/bash

# Startup script for Phase 3 Enhanced Frontend

echo "========================================"
echo "Legal Document Processor - Phase 3"
echo "Enhanced Frontend with Fallback Support"
echo "========================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate

# Install/update requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Start backend server in background
echo "Starting backend server..."
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "Waiting for backend to initialize..."
sleep 5

# Check if backend is running
if ! curl -s http://localhost:8000/ > /dev/null; then
    echo "Error: Backend server failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "Backend server running on http://localhost:8000"

# Start frontend with Phase 3 app
echo "Starting Phase 3 Enhanced Frontend..."
cd frontend
streamlit run streamlit_app_phase3.py --server.port 8501 &
FRONTEND_PID=$!
cd ..

echo "========================================"
echo "Phase 3 Application Started!"
echo "Backend API: http://localhost:8000"
echo "Frontend UI: http://localhost:8501"
echo "========================================"
echo ""
echo "Features available:"
echo "- Simple document processing (original)"
echo "- Enhanced processing with fallback documents"
echo "- Complete Phase 4.1 Legal Workflow"
echo "- Requirements extraction and analysis"
echo "- Legal coherence visualization"
echo "- Workflow progress tracking"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for interrupt
trap "echo 'Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait