# Word Document Tracked Changes Chatbot

This project provides a small demo showing how a Word document can be updated with tracked changes suggested by an LLM.  A FastAPI service receives a DOCX file and a text prompt, asks the LLM for edit instructions and then applies those edits with `word_processor.py`.  A simple Streamlit front end lets you upload the file and chat with the backend.

## Running

1. Install the requirements
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `backend/.env.example` to `backend/.env` and edit it to set
   `AI_PROVIDER` and the API keys for that provider. Also copy
   `frontend/.env.example` to `frontend/.env`.
3. Start the backend
   ```bash
   uvicorn backend.main:app --reload
   ```
4. In another terminal start the Streamlit app
   ```bash
   streamlit run frontend/streamlit_app.py
   ```

Open the URL shown by Streamlit and upload a `.docx` file. Type instructions in the chat box and a download link for the edited document will appear in the assistant response.

## Project Structure

- `backend/`: Contains the FastAPI backend application.
  - `main.py`: FastAPI endpoints for processing documents.
  - `llm_handler.py`: Handles communication with the configured AI provider.
  - `ai_client.py`: LiteLLM-based client supporting multiple providers.
  - `config.py`: Provider settings and application configuration.
  - `word_processor.py`: Core script for manipulating Word documents.
- `frontend/`: Contains the Streamlit frontend application.
  - `streamlit_app.py`: The user interface.
- `requirements.txt`: Lists the Python dependencies for the project.

## Setup and Running

### Prerequisites

- Python 3.8+
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
    source source venv/Scripts/activate # Use On Windows use 
    # source venv/bin/activate  # Use on Unix, Mac, WSL systems
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure your AI provider:**
    Copy `backend/.env.example` to `backend/.env` and edit the values:
    ```
    AI_PROVIDER=openai  # or azure_openai, anthropic, google
    OPENAI_API_KEY="your_openai_api_key_here"
    # Other provider keys are also supported
    ```
    These `.env` files are ignored by git and should not be committed.
    Alternatively, you can set the variables in your shell environment.

### Running the Application

1.  **Start the FastAPI backend:**
    From the project root (not inside backend/), run:
    ```bash
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
    ```

2.  **Start the Streamlit frontend:**
    In a new terminal, from the project root, run:
    ```bash
    streamlit run frontend/streamlit_app.py
    ```
    > Note: If you see an error about `st.experimental_rerun`, update Streamlit to a recent version; the code now uses `st.rerun()`.

Open your browser and go to the URL provided by Streamlit (usually `http://localhost:8501`).

### Configuring the Backend URL

The frontend looks for a `BACKEND_URL` environment variable to know where the FastAPI service is running. If this variable is not set, it defaults to `http://localhost:8000`. When deploying the backend to a different host (for example on Azure), set this variable before starting Streamlit:

```bash
export BACKEND_URL="https://your-backend.example.com"
streamlit run streamlit_app.py
```

### Local Testing

With the backend running on `http://localhost:8000` and the frontend started as shown above (without setting `BACKEND_URL`), you can test the application locally by visiting `http://localhost:8501` in your browser and uploading a `.docx` file.

### Running on Azure

To deploy the demo to Azure you will typically create two separate Web Apps (or container apps) - one for the FastAPI backend and one for the Streamlit frontend.

1. **Backend**
   - Deploy the code in the `backend/` directory to an Azure Web App.
   - In the Azure portal, add an application setting named `OPENAI_API_KEY` containing your OpenAI key. The backend reads this value at startup.

2. **Frontend**
   - Deploy the contents of the `frontend/` directory to another Web App or to Azure Static Web Apps.
   - Configure an application setting `BACKEND_URL` pointing to the public URL of the backend service (e.g. `https://<your-backend>.azurewebsites.net`).
   - The Streamlit app will use this value to send requests to the backend.

After both services are deployed and the environment variables are configured, navigate to the frontend's URL and use the app as you would locally.

## How it Works

1.  The user uploads a `.docx` file and types a description of the desired checks/changes in the Streamlit UI.
    Users can optionally click **Analyze Document for Suggestions** to have the LLM
    provide a short numbered summary of potential improvements before giving
    editing instructions.
2.  Streamlit sends this data to the FastAPI backend.
3.  The backend calls the configured AI provider (`llm_handler.py` / `ai_client.py`) with the document content (or a summary) and the user's instructions. It requests the model to return a list of specific text changes in a predefined JSON format.
4.  The LLM's JSON response is then passed to the `word_processor.py` script along with the original Word document.
5.  `word_processor.py` applies these changes to the document, creating tracked revisions and comments.
6.  The backend returns the processed document and any logs to the Streamlit frontend.
7.  Streamlit allows the user to download the modified Word document and view any processing logs.

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

