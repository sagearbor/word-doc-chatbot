# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Word Document Tracked Changes Chatbot that allows users to upload DOCX files and apply AI-suggested edits with tracked changes. The system consists of a FastAPI backend and a SvelteKit frontend, supporting multiple AI providers (OpenAI, Azure OpenAI, Anthropic, Google) via LiteLLM. The SvelteKit frontend provides a modern, high-performance user interface with TypeScript, mobile support, and sub-second load times.

## Key Commands

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment file (single .env in project root)
cp .env.example .env
# Edit .env to set CURRENT_AI_PROVIDER and API keys for your chosen provider
# Example for Azure OpenAI:
#   CURRENT_AI_PROVIDER=azure_openai
#   AZURE_OPENAI_API_KEY=your-key
#   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
#   AZURE_OPENAI_DEFAULT_DEPLOYMENT_NAME=gpt-5-mini
```

### Running the Application

#### Local Development
```bash
# Install Python dependencies (backend)
pip install -r requirements.txt

# Install Node.js dependencies (frontend)
cd frontend-new
npm install
cd ..

# Start the FastAPI backend (from project root)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Start the SvelteKit frontend (in separate terminal from frontend-new/)
cd frontend-new
npm run dev
# Frontend runs on http://localhost:5173
```

#### Frontend Development Commands
```bash
cd frontend-new

# Start dev server with HMR
npm run dev

# Build for production
npm run build

# Preview production build
npm preview

# Type checking
npm run check

# Type checking in watch mode
npm run check:watch
```

#### Docker Deployment
```bash
# IMPORTANT: Ensure .env file exists in project root first!

# Build the single-container SvelteKit application
docker build -f Dockerfile.sveltekit -t word-chatbot:sveltekit .

# Run the container (serves both frontend and backend)
docker run -d -p 3004:8000 --env-file .env --name word-chatbot word-chatbot:sveltekit

# View logs
docker logs -f word-chatbot

# Stop container
docker stop word-chatbot

# Remove container
docker rm word-chatbot

# Access:
# - Full application: http://localhost:3004
# - Backend API docs: http://localhost:3004/docs
# - Health check: http://localhost:3004/health
```

**Key improvements with SvelteKit deployment:**
- Single container instead of 3 (backend, frontend, nginx-helper)
- FastAPI serves static SvelteKit build files
- No docker-compose required
- No nginx-helper needed (SvelteKit handles base paths natively)
- Simplified environment variable management
- Faster startup and lower resource usage

## Specialized Agents

This project has configured specialized agents in `.claude/agents/` that should be used proactively for specific tasks. **Always prefer using these agents over doing the work manually** as they provide systematic, tested approaches to common development activities.

### When to Use Each Agent

#### 1. **code-simplifier** - Repository Cleanup & Code Quality
**Use for:**
- Cleaning up repository structure and removing clutter
- Removing duplicate code across modules
- Identifying and removing orphaned/unused code
- Simplifying overly complex functions
- After completing features (cleanup before merge)
- Before major releases

**Example invocations:**
```
"Let's clean up the root directory - it's getting cluttered"
→ Use code-simplifier agent to reorganize files systematically

"I just finished the new feature, can you review it for cleanup?"
→ Use code-simplifier agent to check for duplication and complexity

"The repo feels messy, can you tidy it up?"
→ Use code-simplifier agent for comprehensive cleanup
```

**Key features:**
- Maintains `.code-simplifier-tracking.json` to track reviews
- Always runs tests before/after changes
- Reverts changes if tests fail
- Provides detailed reports of all modifications

#### 2. **tech-lead-developer** - Feature Implementation
**Use for:**
- Implementing new features or modules
- Creating independent API endpoints
- Building isolated UI components
- Writing independent utility functions
- **Can run multiple in parallel** for independent tasks

**Example invocations:**
```
"I need three new API endpoints: /export/, /validate/, /stats/"
→ Launch 3 tech-lead-developer agents in parallel

"Create SvelteKit components for upload, analysis, and results"
→ Launch multiple tech-lead-developer agents for each component

"Implement the legal document processor module"
→ Use tech-lead-developer agent for focused implementation
```

**Key features:**
- Can work on branches and commit changes
- Excels at parallel independent development
- Follows project patterns in CLAUDE.md
- Creates comprehensive implementations

#### 3. **qc-test-maintainer** - Testing & Quality Assurance
**Use for:**
- Creating test suites after implementing features
- Updating tests after code changes
- Running comprehensive test verification
- Adding tests for edge cases
- Ensuring test coverage

**Example invocations:**
```
"I just added /process-legal-document/ endpoint"
→ Use qc-test-maintainer to create comprehensive tests

"Run all tests to verify nothing broke"
→ Use qc-test-maintainer to execute full test suite

"The word processor was updated, ensure tests cover new behavior"
→ Use qc-test-maintainer to update and verify tests
```

**Key features:**
- Automatically identifies related test files
- Runs tests and reports results
- Creates missing test coverage
- Updates tests when code changes

#### 4. **ux-reviewer** - UI/UX Evaluation
**Use for:**
- Reviewing UI implementations for visual appeal
- Checking cross-platform/mobile compatibility
- Evaluating user experience and intuitiveness
- Ensuring accessibility compliance
- After implementing any user-facing features

**Example invocations:**
```
"I've implemented the SvelteKit file upload component"
→ Use ux-reviewer to evaluate UX and mobile-friendliness

"Review the new dashboard layout for usability"
→ Use ux-reviewer to assess design and accessibility

"Check if the new button works well on mobile"
→ Use ux-reviewer for cross-platform evaluation
```

**Key features:**
- Evaluates without adding unnecessary code
- Checks mobile/tablet/desktop compatibility
- Verifies accessibility (WCAG compliance)
- Provides actionable UX recommendations

#### 5. **security-reviewer** - Security Audits
**Use for:**
- Reviewing file upload endpoints
- Checking API key and secrets management
- Auditing authentication/authorization
- Reviewing Docker/deployment configurations
- After implementing data handling features
- Before production deployments

**Example invocations:**
```
"I added a file upload endpoint for .docx files"
→ Use security-reviewer to check for vulnerabilities

"Updated environment variable handling for API keys"
→ Use security-reviewer to audit secrets management

"Here's the new Dockerfile for production"
→ Use security-reviewer to check deployment security
```

**Key features:**
- Identifies common vulnerabilities (XSS, injection, etc.)
- Reviews secrets management
- Checks Docker security (non-root users, exposed ports)
- Provides remediation recommendations

### Best Practices for Agent Usage

1. **Proactive invocation**: Don't wait to be asked - use agents when appropriate tasks arise
2. **Parallel execution**: Launch multiple `tech-lead-developer` agents for independent tasks
3. **Sequential workflow**:
   - Implement with `tech-lead-developer`
   - Test with `qc-test-maintainer`
   - Review UX with `ux-reviewer`
   - Audit security with `security-reviewer`
   - Clean up with `code-simplifier`
4. **Trust agent outputs**: Agents are specialized and tested - their recommendations should be followed
5. **Documentation**: Agents maintain their own tracking files (e.g., `.code-simplifier-tracking.json`)

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
# SvelteKit handles base paths natively - no nginx-helper required!
# See NGINX_DEPLOYMENT_GUIDE.md for complete setup instructions

# Set BASE_URL_PATH environment variable
export BASE_URL_PATH=/sageapp04

# Build and run the container
docker build -f Dockerfile.sveltekit -t word-chatbot:sveltekit .
docker run -d -p 8000:8000 --env-file .env word-chatbot:sveltekit

# NGINX configuration (IT-managed)
# location /sageapp04 {
#     proxy_pass http://127.0.0.1:8000;
#     # WebSocket support
#     proxy_http_version 1.1;
#     proxy_set_header Upgrade $http_upgrade;
#     proxy_set_header Connection "upgrade";
#     # ... standard headers
# }
```

**SIMPLIFIED**: No nginx-helper container needed with SvelteKit!
- SvelteKit's adapter-static handles base paths at build time
- Frontend assets use correct paths automatically
- Single container deployment
- Easier troubleshooting and maintenance

#### Docker Production Deployment
```bash
# Build for production
docker build -f Dockerfile.sveltekit -t word-chatbot:production .

# Run in production mode
docker run -d \
  -p 8000:8000 \
  --env-file .env.production \
  --restart unless-stopped \
  --name word-chatbot-prod \
  word-chatbot:production

# Deploy to Azure Container Registry
# See DOCKER_DEPLOYMENT.md for complete deployment instructions

# Environment variables for production (set in .env.production file)
# - CURRENT_AI_PROVIDER: openai, azure_openai, anthropic, or google
# - API keys for chosen provider (e.g., AZURE_OPENAI_API_KEY)
# - BASE_URL_PATH: Path prefix if behind reverse proxy (optional, e.g., /sageapp04)
# - ENVIRONMENT: production
# - PUBLIC_BACKEND_URL: Frontend API client URL (for SvelteKit)
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

### Frontend Structure (`frontend-new/`)
- **SvelteKit application** with TypeScript, TailwindCSS, and Skeleton UI
- **src/routes/**: SvelteKit file-based routing
  - `+page.svelte`: Main application page with tabbed interface
  - `+layout.svelte`: Root layout with dark mode support
- **src/lib/components/**: Reusable Svelte components
  - `DocumentUpload.svelte`: File upload with drag-and-drop
  - `ProcessingOptions.svelte`: LLM configuration and debug options
  - `ProcessingResults.svelte`: Results display with download
  - `ProcessingLogs.svelte`: Detailed processing logs viewer
  - `AnalysisResults.svelte`: Document analysis results
  - `Header.svelte`: Application header with dark mode toggle
  - `Footer.svelte`: Application footer
  - `Toast.svelte`: Notification system
- **src/lib/stores/**: Svelte stores for state management
  - `documentStore.ts`: Document state (main file, fallback file)
  - `processingStore.ts`: Processing state and results
  - `uiStore.ts`: UI state (dark mode, active tab, toasts)
- **src/lib/api/**: API client and utilities
  - `client.ts`: FastAPI backend communication
  - `types.ts`: TypeScript interfaces and types
- **src/lib/utils/**: Utility functions
  - `index.ts`: Common utilities and helpers

**Legacy frontend** (`frontend/`):
- **streamlit_app.py**: Deprecated Streamlit interface
- Maintained for backward compatibility only
- Use SvelteKit frontend for all new development

### Legal Document Processing System
The project includes advanced legal document processing with multiple phases:
- **Phase 1.1**: Legal Document Parser (`legal_document_processor.py`)
- **Phase 2.1**: Requirements Extraction (`requirements_processor.py`) 
- **Phase 2.2**: Advanced Instruction Merging (`instruction_merger.py`)
- **Phase 4.1**: Complete Workflow Orchestration (`legal_workflow_orchestrator.py`)

### Core Processing Flow

#### Standard Processing Mode
1. User uploads DOCX file via SvelteKit interface
2. Frontend sends file to FastAPI backend via API client
3. Backend extracts text using `_build_visible_text_map()` from word_processor
4. LLM generates structured JSON edits with contextual and specific text identification
5. Word processor applies changes as tracked revisions with precise XML manipulation
6. Modified document and logs returned to frontend
7. User downloads processed document from SvelteKit UI

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
- Frontend API client handles connection errors, timeouts, and HTTP errors gracefully
- Toast notifications for user-facing errors
- Processing logs track ambiguous changes and failures
- TypeScript interfaces ensure type safety across frontend

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

### SvelteKit Frontend Patterns

#### State Management
- **Svelte stores** for reactive state (document, processing, UI state)
- **Writable stores** with TypeScript interfaces
- Store subscriptions in components for reactive updates
- Centralized state prevents prop drilling

Example:
```typescript
import { documentStore } from '$lib/stores/documentStore';

// Update state
documentStore.set({ mainFile: file, fallbackFile: null });

// Subscribe to state
$: currentDoc = $documentStore.mainFile;
```

#### API Client Usage
- Centralized API client in `src/lib/api/client.ts`
- All backend communication goes through typed functions
- Automatic base path handling from environment
- Error handling with typed responses

Example:
```typescript
import { processDocument } from '$lib/api/client';

const result = await processDocument(formData);
if (result.error) {
  // Handle error
} else {
  // Process result
}
```

#### Component Structure
- **Presentation components**: Pure UI, receive props
- **Container components**: Connect to stores, handle logic
- **Composition**: Small, focused components composed together
- **TypeScript**: All components use TypeScript for props and events

Example component structure:
```svelte
<script lang="ts">
  import type { ProcessingResult } from '$lib/api/types';

  interface Props {
    result: ProcessingResult;
  }

  let { result }: Props = $props();
</script>

<div class="component">
  <!-- UI markup -->
</div>
```

#### Styling Patterns
- **TailwindCSS** for utility-first styling
- **Skeleton UI** theme system for consistent design
- **Dark mode** support via class-based switching
- **Responsive design** with Tailwind breakpoints

#### Form Handling
- Native FormData for file uploads
- Reactive form validation with Svelte stores
- Progressive enhancement where possible
- Loading states during async operations

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
- SvelteKit uses `PUBLIC_BACKEND_URL` for API client configuration (build-time variable)
- Temporary file handling with automatic cleanup
- Debug mode flags for verbose processing logs

### Reverse Proxy Configuration
- `BASE_URL_PATH`: Set when deploying behind reverse proxy with path prefix (e.g., `/sageapp04`)
- SvelteKit adapter-static handles base paths at build time (configured in svelte.config.js)
- No nginx-helper required - SvelteKit assets use correct paths automatically
- See NGINX_DEPLOYMENT_GUIDE.md for simplified NGINX setup instructions

### Environment Variables

#### Backend (.env file)
- `CURRENT_AI_PROVIDER`: openai, azure_openai, anthropic, or google
- Provider-specific API keys (e.g., `AZURE_OPENAI_API_KEY`)
- Model configuration (e.g., `AZURE_OPENAI_DEFAULT_DEPLOYMENT_NAME`)
- `BASE_URL_PATH`: Path prefix for reverse proxy deployment (optional)

#### Frontend (frontend-new/.env)
- `PUBLIC_BACKEND_URL`: Backend API URL for development/production
  - Development: `http://localhost:8000`
  - Production: `http://localhost:8000` or custom domain
- `BASE_URL_PATH`: Must match backend setting for reverse proxy deployments

#### Docker Deployment
- Single container serves both frontend and backend
- Environment variables from root `.env` file
- No docker-compose or nginx-helper needed
- See `.env.example` for all available options

When working with this codebase, prioritize understanding:
1. **word_processor.py** XML manipulation logic for tracked changes
2. **Multi-provider AI configuration** via LiteLLM
3. **Tracked changes extraction** from fallback documents (TrackedChange dataclass)
4. **SvelteKit architecture** with stores, components, and API client
5. **Simplified deployment** with single Docker container (no nginx-helper)

## Documentation Files

- **NGINX_DEPLOYMENT_GUIDE.md**: Simplified NGINX reverse proxy setup (no nginx-helper needed with SvelteKit)
- **DOCKER_DEPLOYMENT.md**: Single-container Docker deployment guide
- **FALLBACK_TRACKED_CHANGES.md**: Complete documentation for tracked changes extraction feature
- **SVELTEKIT_MIGRATION.md**: Details on the Streamlit to SvelteKit migration
- **README.md**: General project information and getting started guide
- **CLAUDE.md** (this file): Developer guidance for working with the codebase
- **frontend-new/README.md**: SvelteKit frontend-specific documentation