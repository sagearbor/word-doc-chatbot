# Word Document Tracked Changes Chatbot

This application allows users to upload a Word document, provide instructions for changes,
and receive a new Word document with those changes applied as tracked revisions.
The application uses an LLM (OpenAI GPT) to interpret the instructions and generate
the specific edits, which are then applied by a Python script.

## Project Structure

- `backend/`: Contains the FastAPI backend application.
  - `main.py`: FastAPI endpoints for processing documents.
  - `llm_handler.py`: Handles communication with the OpenAI API.
  - `word_processor.py`: Core script for manipulating Word documents.
- `frontend/`: Contains the Streamlit frontend application.
  - `streamlit_app.py`: The user interface.
- `.gitignore`: Specifies intentionally untracked files that Git should ignore.
- `requirements.txt`: Lists the Python dependencies for the project.
- `Dockerfile`: For building a Docker container (optional).

## Setup and Running

### Prerequisites

- Python 3.8+
- An OpenAI API Key

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-name>
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your OpenAI API Key:**
    Create a file named `.env` in the `backend/` directory with your OpenAI API key:
    ```
    OPENAI_API_KEY="your_openai_api_key_here"
    ```
    Alternatively, you can set it as an environment variable.

### Running the Application

1.  **Start the FastAPI backend:**
    Navigate to the `backend` directory and run:
    ```bash
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```

2.  **Start the Streamlit frontend:**
    In a new terminal, navigate to the `frontend` directory and run:
    ```bash
    streamlit run streamlit_app.py
    ```

Open your browser and go to the URL provided by Streamlit (usually `http://localhost:8501`).

### Configuring the Backend URL

The frontend looks for a `BACKEND_URL` environment variable to know where the FastAPI service is running. If this variable is not set, it defaults to `http://localhost:8000`. When deploying the backend to a different host (for example on Azure), set this variable before starting Streamlit:

```bash
export BACKEND_URL="https://your-backend.example.com"
streamlit run streamlit_app.py
```

### Local Testing

With the backend running on `http://localhost:8000` and the frontend started as shown above (without setting `BACKEND_URL`), you can test the application locally by visiting `http://localhost:8501` in your browser and uploading a `.docx` file.

## How it Works

1.  The user uploads a `.docx` file and types a description of the desired checks/changes in the Streamlit UI.
2.  Streamlit sends this data to the FastAPI backend.
3.  The backend calls the OpenAI API (`llm_handler.py`) with the document content (or a summary) and the user's instructions. It requests OpenAI to return a list of specific text changes in a predefined JSON format.
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
