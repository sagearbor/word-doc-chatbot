@echo off
echo ========================================
echo Legal Document Processor - Phase 3
echo Enhanced Frontend with Fallback Support
echo ========================================

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update requirements
echo Installing requirements...
pip install -r requirements.txt

REM Start backend server in new window
echo Starting backend server...
start "Backend Server" cmd /k "cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Wait for backend to start
echo Waiting for backend to initialize...
timeout /t 10 /nobreak >nul

REM Start frontend with Phase 3 app in new window
echo Starting Phase 3 Enhanced Frontend...
start "Frontend App" cmd /k "cd frontend && streamlit run streamlit_app_phase3.py --server.port 8501"

echo ========================================
echo Phase 3 Application Started!
echo Backend API: http://localhost:8000
echo Frontend UI: http://localhost:8501
echo ========================================
echo.
echo Features available:
echo - Simple document processing (original)
echo - Enhanced processing with fallback documents
echo - Complete Phase 4.1 Legal Workflow
echo - Requirements extraction and analysis
echo - Legal coherence visualization
echo - Workflow progress tracking
echo.
echo Close this window and the server windows to stop the application
pause