# Project Plan: Fallback Document Feature Development

**Overall Goal:** Implement a fallback document feature that allows users to upload template/baseline Word documents containing minimum contract requirements for automated processing.

**Current Status:** Phase 2.1 Complete ✅ - Advanced Requirements Processing Engine Built

**Progress Tracking:** See PROJECT_PROGRESS.md for detailed development status.

**Phase 1: Resolve Azure API Connection Error (Highest Priority Blocker)**

1.  **User Action: Verify and Correct `AZURE_OPENAI_API_VERSION`**
    *   **Location:** Check your actual `.env` file (likely located at `c:\Users\scb2\Documents\GitHub\word-doc-chatbot\.env`) or your system/user environment variables.
    *   **Variable Name:** `AZURE_OPENAI_API_VERSION`
    *   **Correct Format:** Ensure the value is a valid Azure OpenAI API version string.
        *   Examples: `2024-02-15-preview`, `2023-07-01-preview`.
        *   **Crucially, ensure there are NO extra quotes around the value in the `.env` file.**
            *   Correct: `AZURE_OPENAI_API_VERSION=2024-02-15-preview`
            *   Incorrect: `AZURE_OPENAI_API_VERSION="2024-02-15-preview"`
            *   Incorrect: `AZURE_OPENAI_API_VERSION='"2024"'`
            *   Incorrect: `AZURE_OPENAI_API_VERSION=2024`
2.  **Test Connection:**
    *   After correcting the environment variable, restart your FastAPI application.
    *   Re-run the process with the test document (`simpleDoc_1editor.docx`) and the instruction: `"change MrArbor to MrSage and the cost should be at least $208. Also Bob goes by Robert so replace that."`
3.  **Verify Fix:**
    *   Examine the application logs.
    *   **Expected Outcome:** The `ValueError: invalid literal for int() with base 10: '"2024'` should no longer appear. You should see an attempt to communicate with the LLM. It's okay if the LLM response is still not perfect (e.g., still incomplete or a different error from the LLM itself), but the API connection error must be gone.

**Phase 2: Address LLM Output Incompleteness (Issue #1)**
*(This phase proceeds only after Phase 1 is successfully completed and the API connection error is resolved)*

1.  **Analyze LLM's Raw Response:**
    *   With the connection fixed, inspect the raw JSON response now being returned by the LLM (it should appear in your logs, similar to the `[]` you saw before, but hopefully with content).
    *   Determine if the LLM is returning a single JSON object or an array.
    *   Check if it's attempting to return multiple edit objects or still just one.
2.  **Modify `backend/llm_handler.py`:**
    *   **Adjust `response_format` in `get_chat_response` (line 164):**
        *   The current prompt (lines 151-153) explicitly asks the LLM for a "flat JSON array of objects."
        *   However, the API call uses `response_format={"type": "json_object"}`. This might conflict, potentially forcing the LLM to wrap its array in an object or only return the first element as an object.
        *   **Experiment 1 (Recommended First):** Try removing the `response_format={"type": "json_object"}` parameter entirely from the `get_chat_response` call. This will allow the LLM to send back the array as requested by the prompt.
        *   **Experiment 2 (If Exp1 doesn't work):** If your Azure OpenAI model version *requires* `json_object` mode for reliable JSON, you might need to:
            *   Modify the prompt to ask the LLM to return a JSON object that *contains* the array of edits (e.g., `{"edits": [ {edit1}, {edit2} ]}`).
            *   Update the `_parse_llm_response` function (line 41) to extract the list of edits from this new wrapper object.
    *   **Refine LLM Prompt in `get_llm_suggestions` (line 125 onwards, if needed):**
        *   If, after adjusting `response_format`, the LLM still returns incomplete results, the prompt may need further strengthening.
        *   Consider adding more explicit instructions like: *"You MUST process the *entirety* of the user's instructions. For EACH distinct change requested by the user that you identify in the document, you MUST generate a separate JSON object in the output array. Ensure all aspects of the user's request are addressed."*
3.  **Test and Iterate:**
    *   After each modification to `llm_handler.py`, re-run the test case.
    *   Check the logs for the raw LLM output and the parsed edits.
    *   **Expected Outcome:** The LLM returns a JSON array containing a separate object for each requested change (MrArbor, cost, and all Bob instances).

**Phase 3: Address Secondary Issues**
*(To be tackled once the LLM is consistently providing complete and correctly formatted edit instructions)*

1.  **Issue #2: Word Processor - Context Matching Failure:**
    *   Once the LLM provides an edit instruction for "MrArbor" (and others), this issue can be properly re-tested.
    *   The detailed string comparison logic already added to `backend/word_processor.py` will be key to diagnosing any subtle differences if matching still fails.
2.  **Issue #3: Streamlit UI - Ephemeral Status Message:**
    *   Modify `frontend/streamlit_app.py` to ensure status/success/error messages persist long enough for the user to read them. This might involve using `st.session_state` to hold the message until explicitly cleared or a new action is taken.
3.  **Issue #4: Isolated Test Environment for `word_processor.py`:**
    *   Continue developing the `debug_word_processor` folder and `test_script.py`.
    *   This environment will be invaluable for testing the `word_processor.py` logic with known-good, complete JSON edit instructions, bypassing the LLM and FastAPI layers.

**Visual Plan (Mermaid Diagram):**

```mermaid
graph TD
    A[Start: User Task - Automate DOCX Edits] --> B{Current Blocker: LLM Output Incomplete};
    B -- Investigation --> C{Log Analysis: API Connection Error!};
    C --> D[Root Cause: Invalid AZURE_OPENAI_API_VERSION format];

    subgraph Phase 1 [Resolve API Connection]
        direction LR
        D1[User: Verify/Correct .env: AZURE_OPENAI_API_VERSION] --> D2{Test: Re-run App};
        D2 --> D3{API Connection Error Gone?};
    end

    D3 -- Yes --> E[Phase 2: Fix LLM Incompleteness];
    D3 -- No --> D1;

    subgraph Phase 2 [Address LLM Output Incompleteness]
        direction TB
        E1[Analyze LLM Raw JSON Response] --> E2[Modify llm_handler.py: Adjust/Remove `response_format`];
        E2 --> E3[Modify llm_handler.py: Refine Prompt (if needed)];
        E3 --> E4{Test: LLM Returns All Edits in Array?};
    end

    E4 -- Yes --> F[Phase 3: Tackle Secondary Issues];
    E4 -- No --> E1;

    subgraph Phase 3 [Address Secondary Issues]
        direction TB
        F1[Issue #2: Word Processor Context Matching]
        F2[Issue #3: Streamlit UI Ephemeral Message]
        F3[Issue #4: Isolated Test Env for Word Processor]
    end
    F --> F1;
    F --> F2;
    F --> F3;

    F1 & F2 & F3 --> G[End: System Behaves as Expected];
