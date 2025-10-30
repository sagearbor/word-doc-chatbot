# Word Document Tracked Changes Chatbot

This project provides a modern web application for applying AI-suggested edits to Word documents with tracked changes. A FastAPI backend receives DOCX files and text prompts, uses LLMs to generate edit instructions, and applies those edits with `word_processor.py`. A SvelteKit frontend provides a fast, responsive user interface with full mobile support.

## Running

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Install frontend dependencies:
   ```bash
   cd frontend-new
   npm install
   cd ..
   ```
3. Copy `.env.example` to `.env` in the project root and set your AI provider credentials.  
   Optional: copy `frontend-new/.env.example` to `frontend-new/.env.development` if you need to override the default frontend environment values.
4. Start the FastAPI backend from the project root:
   ```bash
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```
5. In another terminal start the SvelteKit frontend:
   ```bash
   cd frontend-new
   npm run dev
   ```

Open `http://localhost:5173` to use the application. The frontend is configured to talk to the backend at `http://localhost:8000` by default.

> **Note:** The legacy Streamlit UI has been retired. If you need to reference it, check the git history.

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework for building APIs
- **python-docx**: Word document manipulation with XML-level control
- **LiteLLM**: Multi-provider AI integration (OpenAI, Azure, Anthropic, Google)
- **pytest**: Comprehensive testing framework

### Frontend
- **SvelteKit**: High-performance web framework with TypeScript
- **TailwindCSS**: Utility-first CSS framework
- **Skeleton UI**: Component library for SvelteKit
- **Lucide Icons**: Modern icon library

### Performance Highlights
- Bundle size: ~50KB gzipped (vs ~2MB with Streamlit)
- Page load time: <1s (vs 3-5s with Streamlit)
- Mobile-first responsive design
- Dark mode support
- Concurrent user support: 1000+

## Project Structure

- `backend/`: FastAPI backend application
  - `main.py`: API endpoints for document processing
  - `llm_handler.py`: AI provider communication layer
  - `ai_client.py`: LiteLLM-based multi-provider client
  - `config.py`: Configuration and settings management
  - `word_processor.py`: Core Word document manipulation
- `frontend-new/`: SvelteKit frontend application
  - `src/routes/`: SvelteKit page routes
  - `src/lib/components/`: Reusable Svelte components
  - `src/lib/stores/`: Svelte stores for state management
  - `src/lib/api/`: API client and utilities
- `archive/`: Historical assets and experiments (the retired Streamlit UI exists only in older commits)
- `requirements.txt`: Python dependencies

## Setup and Running

### Prerequisites

- Python 3.8+
- Node.js 18+ and npm (for frontend development)
- An API key for your chosen provider (OpenAI, Azure, Anthropic, etc.)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-name>
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # macOS/Linux/WSL
    # On Windows (PowerShell):
    # .\venv\Scripts\Activate.ps1
    ```



3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure your AI provider:**
    Copy `.env.example` to `.env` in the project root and edit the values:
    ```
    AI_PROVIDER=openai  # or azure_openai, anthropic, google
    OPENAI_API_KEY="your_openai_api_key_here"
    # Other provider keys are also supported
    ```
    These `.env` files are ignored by git and should not be committed.
    Alternatively, you can set the variables in your shell environment.
    Optional: copy `frontend-new/.env.example` to `frontend-new/.env.development` if you need to override frontend defaults.

### Running the Application

#### Backend Development

1.  **Start the FastAPI backend:**
    From the project root (not inside backend/), run:
    ```bash
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
    ```

The backend API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

#### Frontend Development

1.  **Install frontend dependencies:**
    ```bash
    cd frontend-new
    npm install
    ```

2.  **Start the development server:**
    ```bash
    npm run dev
    ```

The frontend will be available at `http://localhost:5173` with hot module replacement enabled.

#### Full Stack Development

For full-stack development, run both the backend and frontend in separate terminals:

```bash
# Terminal 1: Backend
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend-new && npm run dev
```

Open your browser to `http://localhost:5173` to access the application.

### Docker Deployment

#### Quick Deployment (Recommended)

Deploy with a single command using the deployment script:

```bash
# One-command deployment (stops old container, rebuilds, starts on port 3004)
./deploy.sh
```

**Wait ~2-3 minutes for build to complete.**

The script will:
1. Stop and remove any existing container named `word-chatbot`
2. Build the Docker image with no cache
3. Start the container on port 3004
4. Verify successful deployment

**Access:** `http://localhost:3004`

**Port Conflict?** If you see "port is already allocated", stop the old container first:
```bash
# Find container using port 3004
docker ps -a | grep 3004

# Stop and remove it (replace CONTAINER_NAME with actual name)
docker stop CONTAINER_NAME && docker rm CONTAINER_NAME

# Then re-run deployment
./deploy.sh
```

**Quick commands:**
```bash
# View logs
docker logs -f word-chatbot

# Stop container
docker stop word-chatbot

# Start container
docker start word-chatbot

# Restart container
docker restart word-chatbot
```

#### Manual Deployment (Alternative)

If you prefer manual control:

```bash
# Stop and remove old container
docker stop word-chatbot && docker rm word-chatbot

# Build image (no cache) and start
docker build --no-cache -f Dockerfile.sveltekit -t word-chatbot:v0.3 . && \
docker run -d -p 3004:8000 --env-file .env --name word-chatbot --restart unless-stopped word-chatbot:v0.3

# View logs
docker logs -f word-chatbot
```

#### Deployment Details

**Key benefits of single-container deployment:**
- Simplified architecture (no docker-compose needed)
- No nginx-helper container required
- FastAPI serves both API and static frontend files
- Smaller deployment footprint
- Easier maintenance and debugging

**Environment variables:**
- Set in `.env` file in project root
- See `.env.example` for all available options
- Required: AI provider configuration (API keys, endpoints)
- Optional: `BASE_URL_PATH` for reverse proxy deployment (e.g., `/sageapp04`)

**Port mapping:**
- Internal: Container runs on port 8000
- External: Mapped to port 3004 (configurable in deploy.sh)

### Production Deployment

For production deployment, the application uses a single Docker container:

```bash
# Build production image
docker build -f Dockerfile.sveltekit -t word-chatbot:production .

# Run with production environment
docker run -d \
  -p 8000:8000 \
  --env-file .env.production \
  --name word-chatbot-prod \
  word-chatbot:production
```

**NGINX reverse proxy configuration:**
SvelteKit handles base path natively, so no nginx-helper is needed:

```nginx
location /sageapp04 {
    proxy_pass http://127.0.0.1:8000;

    # WebSocket support
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";

    # Standard headers
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Set `BASE_URL_PATH=/sageapp04` in your environment variables for path-based deployment.

See `DOCKER_DEPLOYMENT.md` for detailed deployment guides for various scenarios.

## How it Works

1.  The user uploads a `.docx` file and provides instructions via the SvelteKit UI.
    Users can optionally analyze the document first to get LLM suggestions before processing.
2.  The SvelteKit frontend sends the file and instructions to the FastAPI backend via the API client.
3.  The backend calls the configured AI provider (`llm_handler.py` / `ai_client.py`) with the document content and user instructions. The LLM returns structured JSON edits.
4.  The LLM's JSON response is passed to `word_processor.py` along with the original Word document.
5.  `word_processor.py` applies changes using XML-level manipulation, creating tracked revisions and comments.
6.  The backend returns the processed document and processing logs to the frontend.
7.  The user can download the modified Word document and view detailed processing logs.

**Special modes:**
- **Tracked Changes Mode**: Upload a fallback document with tracked changes - they're extracted and applied directly (faster, no LLM needed)
- **Requirements Mode**: Upload a fallback document with requirements text - merged with user instructions for comprehensive edits
- **Analysis Mode**: View existing tracked changes in documents with summary and raw XML views

## Expected JSON format for Edits

The LLM is prompted to return a JSON list of objects, where each object has the following structure:

```json
[
  {
    "contextual_old_text": "The broader sentence or phrase where the change should occur. This helps locate the specific text if it's not unique.",
    "specific_old_text": "The exact text string to be deleted.",
    "specific_new_text": "The exact text string to be inserted.",
    "reason_for_change": "A brief explanation from the LLM why this change is being made."
  }
]
