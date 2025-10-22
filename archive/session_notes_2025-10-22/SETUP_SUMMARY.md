# Word Doc Chatbot - Setup Summary

**Date**: 2025-10-22

## Issues Fixed

### 1. Connection Error (RESOLVED)
- **Problem**: Frontend couldn't connect to backend (port mismatch + dependency error)
- **Root Cause**:
  - Port 8000 was occupied by JupyterHub
  - `openai==1.6.1` too old for `litellm==1.76.1`
- **Solution**:
  - Upgraded `openai` to 2.6.0 and `tiktoken` to 0.12.0
  - Changed ports to 8004 (backend) and 3004 (frontend)
  - Updated `.env` and `frontend/streamlit_app.py`

### 2. Model Upgrade (COMPLETED)
- **Changed**: `gpt-4o-mini` → `gpt-5-nano`
- **Configuration**: Updated `.env` file deployment names
- **Benefits**: 128K max output tokens (vs 16K for GPT-4)

## Configuration

### Ports
- **Backend**: http://localhost:8004
- **Frontend**: http://localhost:3004
- **API Docs**: http://localhost:8004/docs

### Environment Files
- **Single .env file**: Located at project root (`.env`)
- **Backend** reads from root `.env` (via `backend/config.py`)
- **Frontend** uses environment variables from shell

## Startup Scripts Created

### Quick Start
```bash
# Start both services
./start.sh

# Stop both services
./stop.sh

# Or use Makefile
make start
make stop
```

### Manual Start
```bash
# Terminal 1 - Backend
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8004

# Terminal 2 - Frontend
streamlit run frontend/streamlit_app.py --server.port 3004
```

### Makefile Commands
```bash
make help          # Show all available commands
make start         # Start both services
make stop          # Stop both services
make restart       # Restart both services
make backend       # Start only backend
make frontend      # Start only frontend
make test          # Run tests
make logs          # View logs from both services
make status        # Check service status
make clean         # Clean up temp files
make urls          # Display service URLs
```

## Log Files
- Backend: `/tmp/word-doc-backend.log`
- Frontend: `/tmp/word-doc-frontend.log`
- View logs: `make logs` or `tail -f /tmp/word-doc-backend.log`

## Package Upgrades Applied
```
openai: 1.6.1 → 2.6.0
tiktoken: 0.5.2 → 0.12.0
```

## GPT-5 Model Compatibility Fix

**Issue**: GPT-5 models don't support `temperature=0.0` (only `temperature=1`)

**Solution**: Added `litellm.drop_params = True` in `backend/ai_client.py` to automatically drop unsupported parameters for different models. This allows the code to work seamlessly across GPT-4 and GPT-5 models without modification.

## Current Configuration

### AI Model
- **Provider**: Azure OpenAI
- **Deployment**: gpt-5-nano
- **Max Output Tokens**: 128,000
- **Endpoint**: https://ai-sandbox-instance.openai.azure.com/

### Warnings (Can Ignore)
- `langchain-openai` version conflicts - not used in this project

## Next Steps

1. **Restart backend** to pick up new GPT-5-nano configuration:
   ```bash
   ./stop.sh
   ./start.sh
   ```

2. **Test the connection** by uploading a document in the frontend

3. **Monitor logs** if you encounter issues:
   ```bash
   make logs
   ```

## Troubleshooting

### Backend won't start
```bash
# Check if port is in use
lsof -i :8004

# View backend logs
cat /tmp/word-doc-backend.log

# Test imports
python -c "from backend.main import app; print('OK')"
```

### Frontend can't connect
```bash
# Verify backend is running
curl http://localhost:8004/docs

# Check frontend configuration
grep BACKEND_URL frontend/streamlit_app.py
```

### Check service status
```bash
make status
```
