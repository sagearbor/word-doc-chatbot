# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Word Document Tracked Changes Chatbot that allows users to upload DOCX files and apply AI-suggested edits with tracked changes. The system consists of a FastAPI backend and a Streamlit frontend, supporting multiple AI providers (OpenAI, Azure OpenAI, Anthropic, Google) via LiteLLM.

## Key Commands

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# Edit these files to set AI_PROVIDER and API keys
```

### Running the Application

#### Local Development
```bash
# Start the FastAPI backend (from project root)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Start the Streamlit frontend (in separate terminal)
streamlit run frontend/streamlit_app.py
```

#### Docker Deployment
```bash
# Build and run all services (backend, frontend, nginx-helper)
docker-compose up --build

# Run in detached mode
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild specific service
docker-compose build backend
docker-compose build frontend
```

### Testing
```bash
# Run all tests
pytest tests/

# Run specific test modules
pytest tests/test_main.py
pytest tests/test_llm_handler.py
pytest tests/test_config.py

# Run tests with coverage
pytest tests/ --cov=backend --cov-report=html
```

### Deployment

#### NGINX Reverse Proxy Deployment
```bash
# The application supports deployment behind NGINX reverse proxy with path prefixes
# See NGINX_DEPLOYMENT_GUIDE.md for complete setup instructions

# Set BASE_URL_PATH environment variable for Streamlit
export BASE_URL_PATH=/sageapp04

# TRAILING_SLASH_CHANGE: Main NGINX configuration determines if nginx-helper is needed
# With trailing slash: location /sageapp04/ { proxy_pass http://127.0.0.1:3004/; }
#   -> Strips prefix, requires nginx-helper to restore it
# Without trailing slash: location /sageapp04 { proxy_pass http://127.0.0.1:3004; }
#   -> Keeps prefix, nginx-helper not needed

# Start nginx-helper (if needed)
docker run -d -p 3004:80 -v $(pwd)/nginx-helper.conf:/etc/nginx/conf.d/default.conf nginx:alpine
```

#### Docker Production Deployment
```bash
# Build for production
docker-compose -f docker-compose.yml build

# Deploy to Azure Web App
# See DOCKER_DEPLOYMENT.md for complete Azure deployment instructions

# Environment variables for production
# - AI_PROVIDER: openai, azure_openai, anthropic, or google
# - API keys for chosen provider
# - BASE_URL_PATH: Path prefix if behind reverse proxy
# - BACKEND_URL: Backend service URL (for frontend)
```

### Development Tools
```bash
# Manual testing of word processor
python backend/word_processor.py --input sample.docx --output output.docx --editsjson '[{"contextual_old_text": "old text", "specific_old_text": "old", "specific_new_text": "new", "reason_for_change": "test"}]'
```

## Architecture Overview

### Backend Structure (`backend/`)
- **main.py**: FastAPI application with multiple endpoints for document processing
  - `/process-document/`: Original document processing with tracked changes
  - `/analyze-document/`: Analyze existing tracked changes in documents
  - `/process-document-with-fallback/`: Enhanced processing with fallback documents (supports tracked changes mode)
  - `/process-legal-document/`: Complete legal workflow (Phase 4.1)
- **word_processor.py**: Core document manipulation using python-docx with XML-level editing
  - `TrackedChange` dataclass for structured change representation
  - `extract_tracked_changes_structured()`: Extract tracked changes from DOCX as structured data
  - `convert_tracked_changes_to_edits()`: Convert TrackedChange objects to edit dictionaries
  - `process_document_with_edits()`: Apply edits as tracked changes with XML manipulation
- **llm_handler.py**: AI provider interface with specialized legal document prompts
- **ai_client.py**: Unified LiteLLM client supporting multiple providers
- **config.py**: Configuration management for AI providers and application settings

### Frontend Structure (`frontend/`)
- **streamlit_app.py**: Main Streamlit interface with dual functionality:
  - Document analysis of existing tracked changes
  - Processing new changes with AI instructions

### Legal Document Processing System
The project includes advanced legal document processing with multiple phases:
- **Phase 1.1**: Legal Document Parser (`legal_document_processor.py`)
- **Phase 2.1**: Requirements Extraction (`requirements_processor.py`) 
- **Phase 2.2**: Advanced Instruction Merging (`instruction_merger.py`)
- **Phase 4.1**: Complete Workflow Orchestration (`legal_workflow_orchestrator.py`)

### Core Processing Flow

#### Standard Processing Mode
1. User uploads DOCX file via Streamlit interface
2. FastAPI backend extracts text using `_build_visible_text_map()` from word_processor
3. LLM generates structured JSON edits with contextual and specific text identification
4. Word processor applies changes as tracked revisions with precise XML manipulation
5. Modified document is returned with processing logs

#### Fallback Document Processing Modes
**Tracked Changes Mode (Preferred):**
1. User uploads main DOCX file and fallback DOCX with tracked changes
2. `extract_tracked_changes_structured()` detects and extracts tracked changes from fallback
3. `convert_tracked_changes_to_edits()` converts TrackedChange objects to edit format
4. Changes applied directly to main document (bypasses LLM - faster and more accurate)
5. Modified document returned with tracked changes from fallback applied

**Requirements Mode (Fallback):**
1. User uploads main DOCX and fallback with requirements text
2. `generate_instructions_from_fallback()` extracts requirements
3. Phase 2.1/2.2 logic merges with user instructions
4. LLM generates edits based on combined requirements
5. Changes applied as tracked revisions

### AI Provider Configuration
The system uses environment variables for AI provider configuration:
- `AI_PROVIDER`: Set to "openai", "azure_openai", "anthropic", or "google"
- Provider-specific API keys and endpoints
- Model selection via environment variables with fallbacks

### Testing Framework
- **pytest**: Main testing framework with async support
- **test_main.py**: FastAPI endpoint testing
- **test_llm_handler.py**: AI provider integration tests
- **golden_dataset/**: Comprehensive test cases for legal document processing
- **golden_dataset_tests.py**: End-to-end testing with expected outputs

## Development Patterns

### Error Handling
- Backend returns structured error responses with "Error_" prefixes
- Frontend handles connection errors, timeouts, and HTTP errors gracefully
- Processing logs track ambiguous changes and failures

### Document Processing
- Text boundary validation ensures changes are properly word-bounded
- Case-sensitive and case-insensitive search options
- Comment addition to tracked changes with author attribution
- Highlight ambiguous changes in orange for user review

### AI Integration
- JSON-structured edit responses with validation
- Contextual text for unique identification
- Specific old/new text pairs with change reasoning
- Fallback handling for provider failures

## Important Implementation Details

### Word Document XML Manipulation
- Direct XML manipulation via python-docx for precise tracked changes
- Preservation of document formatting and structure
- Author and timestamp attribution for tracked changes
- Proper boundary checking for text replacements

### Tracked Changes Extraction from Fallback Documents
- **TrackedChange dataclass**: Structured representation of insertions, deletions, and substitutions
- **XML parsing**: Detects w:ins (insertions) and w:del (deletions) elements in Word document XML
- **Substitution detection**: Pairs deletions with following insertions to identify text replacements
- **Context preservation**: Extracts 50 characters before/after each change for accurate matching
- **Author attribution**: Maintains original author and timestamp from tracked changes
- **Direct application**: Bypasses LLM processing when tracked changes are present (faster, more accurate)
- **Automatic fallback**: Falls back to requirements extraction mode if no tracked changes detected
- See FALLBACK_TRACKED_CHANGES.md for complete feature documentation

### Multi-Provider AI Support
- LiteLLM abstraction layer for consistent API interface
- Environment-based provider switching
- Model-specific parameter handling (temperature, max_tokens)
- Structured JSON response parsing with fallback mechanisms

### Legal Document Workflow
- Hierarchical requirement processing
- Conflict resolution between user instructions and fallback requirements
- Legal coherence scoring and validation
- Audit logging for compliance purposes

## Configuration Notes

- Environment files must be configured for each AI provider used
- Backend URL configuration via `BACKEND_URL` environment variable (frontend uses this to connect to backend)
- Temporary file handling with automatic cleanup
- Debug mode flags for verbose processing logs

### Reverse Proxy Configuration
- `BASE_URL_PATH`: Set when deploying behind reverse proxy with path prefix (e.g., `/sageapp04`)
- Streamlit uses this to generate correct URLs for WebSocket connections and static assets
- See frontend/.streamlit/config.toml for CORS and WebSocket settings
- See NGINX_DEPLOYMENT_GUIDE.md for complete NGINX setup instructions

### Docker Environment Variables
- **Backend container**: AI_PROVIDER, API keys, model selection
- **Frontend container**: BACKEND_URL (defaults to http://backend:8004), BASE_URL_PATH (optional)
- **nginx-helper container**: Only needed when main NGINX strips path prefix (see TRAILING_SLASH_CHANGE comments)
- See .env.example files for complete variable documentation
- See DOCKER_DEPLOYMENT.md for production deployment guides

When working with this codebase, prioritize understanding:
1. **word_processor.py** XML manipulation logic for tracked changes
2. **Multi-provider AI configuration** via LiteLLM
3. **Tracked changes extraction** from fallback documents (TrackedChange dataclass)
4. **NGINX reverse proxy** path handling for deployment scenarios

## Documentation Files

- **NGINX_DEPLOYMENT_GUIDE.md**: Complete guide for NGINX reverse proxy setup with path prefix handling
- **DOCKER_DEPLOYMENT.md**: Docker deployment guide for local dev, POC/demo, production, and Azure
- **FALLBACK_TRACKED_CHANGES.md**: Complete documentation for tracked changes extraction feature
- **README.md**: General project information and getting started guide
- **CLAUDE.md** (this file): Developer guidance for working with the codebase