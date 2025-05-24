# Word Document Tracked Changes Chatbot

This project provides a small demo showing how a Word document can be updated with tracked changes suggested by an LLM.  A FastAPI service receives a DOCX file and a text prompt, asks the LLM for edit instructions and then applies those edits with `word_processor.py`.  A simple Streamlit front end lets you upload the file and chat with the backend.

## Running

1. Install the requirements
   ```bash
   pip install -r requirements.txt
   ```
2. (Optional) create `backend/.env` containing your `OPENAI_API_KEY`.
3. Start the backend
   ```bash
   uvicorn backend.main:app --reload
   ```
4. In another terminal start the Streamlit app
   ```bash
   streamlit run frontend/streamlit_app.py
   ```

Open the URL shown by Streamlit and upload a `.docx` file. Type instructions in the chat box and a download link for the edited document will appear in the assistant response.

