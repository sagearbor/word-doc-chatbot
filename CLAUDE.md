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
```bash
# Start the FastAPI backend (from project root)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Start the Streamlit frontend (in separate terminal)
streamlit run frontend/streamlit_app.py
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
  - `/process-document-with-fallback/`: Enhanced processing with fallback documents
  - `/process-legal-document/`: Complete legal workflow (Phase 4.1)
- **word_processor.py**: Core document manipulation using python-docx with XML-level editing
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
1. User uploads DOCX file via Streamlit interface
2. FastAPI backend extracts text using `_build_visible_text_map()` from word_processor
3. LLM generates structured JSON edits with contextual and specific text identification
4. Word processor applies changes as tracked revisions with precise XML manipulation
5. Modified document is returned with processing logs

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
- Backend URL configuration via `BACKEND_URL` environment variable
- Temporary file handling with automatic cleanup
- Debug mode flags for verbose processing logs

When working with this codebase, prioritize understanding the word_processor.py XML manipulation logic and the multi-provider AI configuration system, as these are the core differentiators of this application.