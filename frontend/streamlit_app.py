import os
import requests
import streamlit as st

# Configuration for the FastAPI backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
#BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
PROCESS_ENDPOINT = f"{BACKEND_URL}/process-document/"
DOWNLOAD_ENDPOINT_PREFIX = f"{BACKEND_URL}/download"
ANALYZE_ENDPOINT = f"{BACKEND_URL}/analyze-document/"

st.set_page_config(layout="wide", page_title="Word Document Editor")

st.title("📄 Word Document Tracked Changes Assistant")
st.markdown("""
Upload a Word document (.docx) and provide instructions for the changes you want.
The AI will interpret your instructions, and the system will apply them as tracked changes.
You can then download the modified document.
""")

# --- Session State Initialization ---
if 'processed_file_url' not in st.session_state: st.session_state.processed_file_url = None
if 'processed_filename' not in st.session_state: st.session_state.processed_filename = None
if 'log_content' not in st.session_state: st.session_state.log_content = None
if 'error_message' not in st.session_state: st.session_state.error_message = None
if 'status_message' not in st.session_state: st.session_state.status_message = None
if 'edits_applied_count' not in st.session_state: st.session_state.edits_applied_count = None
if 'edits_suggested_count' not in st.session_state: st.session_state.edits_suggested_count = None
if 'processing' not in st.session_state: st.session_state.processing = False
if 'analysis_content' not in st.session_state: st.session_state.analysis_content = None
if 'debug_log_from_backend' not in st.session_state: st.session_state.debug_log_from_backend = None


with st.sidebar:
    st.header("⚙️ Options")
    uploaded_file = st.file_uploader("1. Upload your .docx file", type=["docx"], key="file_uploader")

    if st.button("🔍 Analyze Document for Suggestions", disabled=st.session_state.processing or not uploaded_file):
        st.session_state.processing = True
        st.session_state.analysis_content = None 
        st.session_state.error_message = None    
        with st.spinner("Analyzing document with LLM..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            try:
                response = requests.post(ANALYZE_ENDPOINT, files=files, timeout=300)
                response.raise_for_status()
                analysis_result = response.json().get("analysis", "No analysis returned.")
                st.session_state.analysis_content = analysis_result
                st.success("Analysis complete!")
            except Exception as e:
                st.session_state.error_message = f"Analysis failed: {e}"
            finally:
                st.session_state.processing = False
                st.rerun() 

    st.subheader("Author for Changes (Optional)")
    author_name_llm = st.text_input(
        "Name for LLM's changes:",
        value="AI Reviewer",
        help="This name will be used as the author for the tracked changes made by the LLM."
    )

    st.subheader("Search Settings")
    case_sensitive_search = st.checkbox(
        "Case-sensitive search",
        value=True,
        help="If checked, 'Text' and 'text' are treated as different. If unchecked, they are the same."
    )

    st.subheader("Tracked Changes Settings")
    add_comments_to_changes = st.checkbox(
        "Add comments to changes",
        value=True,
        help="If checked, the LLM's reason for change will be added as a comment."
    )

    st.subheader("Debugging (for developers)")
    debug_level_options = {
        "Off": ("off", "No server-side debugging."),
        "Standard Debugging": ("standard", "Logs detailed processing steps to the server console."),
        "Extended Debugging": ("extended", "Logs very verbose details, including full contexts (implies Standard).")
    }
    debug_level_choice = st.selectbox(
        "Server Debugging Level:",
        options=list(debug_level_options.keys()),
        index=0, # Default to "Off"
        format_func=lambda x: f"{x} - {debug_level_options[x][1]}" # Show description in dropdown
    )

    # Translate dropdown choice to boolean flags for the backend
    debug_mode_payload = False
    extended_debug_mode_payload = False
    if debug_level_options[debug_level_choice][0] == "standard":
        debug_mode_payload = True
    elif debug_level_options[debug_level_choice][0] == "extended":
        debug_mode_payload = True
        extended_debug_mode_payload = True
    
    # Option to show debug logs from backend in Streamlit UI (new feature)
    # This would require backend changes to return debug logs in the response.
    # For now, this is just a UI element; backend doesn't support it yet.
    # show_debug_in_ui = st.checkbox("Show server debug log in UI (if available)", value=False, help="Attempts to display server debug output here. Requires backend support.")


user_instructions = st.text_area(
    "2. Describe the checks or changes you want:",
    height=150,
    key="instructions_area",
    placeholder="e.g., 'Change all instances of Mr. Smith to Ms. Jones. Update the project deadline from 2024-01-01 to 2024-02-15.'"
)

if st.session_state.analysis_content and not st.session_state.processing:
    st.markdown("---")
    st.markdown("**LLM Analysis & Suggestions:**")
    st.text_area("", value=st.session_state.analysis_content, height=200, disabled=True, label_visibility="collapsed")
    st.info("You can copy suggestions from above into the instruction box if desired.")


if st.button("✨ Process Document", type="primary", disabled=st.session_state.processing or not uploaded_file or not user_instructions):
    st.session_state.processing = True
    # Clear previous results
    st.session_state.processed_file_url = None
    st.session_state.processed_filename = None
    st.session_state.log_content = None
    st.session_state.error_message = None
    st.session_state.status_message = None
    st.session_state.edits_applied_count = None
    st.session_state.edits_suggested_count = None
    st.session_state.debug_log_from_backend = None # Clear previous backend debug log

    with st.spinner("Processing your document... This may take a moment. Please wait."):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        payload = {
            "instructions": user_instructions,
            "author_name": author_name_llm,
            "case_sensitive": case_sensitive_search,
            "add_comments": add_comments_to_changes,
            "debug_mode": debug_mode_payload,             # Use translated value
            "extended_debug_mode": extended_debug_mode_payload # Use translated value
        }

        try:
            response = requests.post(PROCESS_ENDPOINT, files=files, data=payload, timeout=300)
            response.raise_for_status()

            result = response.json()
            st.session_state.processed_filename = result.get("processed_filename")
            st.session_state.processed_file_url = f"{DOWNLOAD_ENDPOINT_PREFIX}/{st.session_state.processed_filename}" if st.session_state.processed_filename else None
            st.session_state.log_content = result.get("log_content", "No log content received.")
            st.session_state.status_message = result.get("status_message", "Processing finished.")
            st.session_state.edits_applied_count = result.get("edits_applied_count")
            st.session_state.edits_suggested_count = result.get("edits_suggested_count")
            # Potentially get debug log if backend supports it
            # st.session_state.debug_log_from_backend = result.get("backend_debug_log") 


            st.success(st.session_state.status_message)
            if st.session_state.edits_suggested_count is not None and st.session_state.edits_applied_count is not None:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="LLM Edits Suggested", value=st.session_state.edits_suggested_count)
                with col2:
                    st.metric(label="Edits Successfully Applied", value=st.session_state.edits_applied_count)

        except requests.exceptions.HTTPError as errh:
            error_body = "Could not parse error response."
            try: error_body = errh.response.json().get("detail", errh.response.text)
            except ValueError: error_body = errh.response.text if errh.response.text else "Http Error with no details."
            st.session_state.error_message = f"Http Error: {errh.response.status_code} - {error_body}"
        except requests.exceptions.ConnectionError as errc:
            st.session_state.error_message = f"Error Connecting: {errc}\nIs the backend server running at {BACKEND_URL}?"
        except requests.exceptions.Timeout:
            st.session_state.error_message = "Timeout Error: The request took too long to complete."
        except requests.exceptions.RequestException as err:
            st.session_state.error_message = f"Request Exception: {err}"
        except Exception as e:
            st.session_state.error_message = f"An unexpected error occurred: {str(e)}"
        finally:
            st.session_state.processing = False
            st.rerun()

# --- Display Results Area (after processing attempt) ---
if not st.session_state.processing:
    if st.session_state.status_message:
        # Determine the type of message for styling (optional)
        if "success" in st.session_state.status_message.lower() or \
           (st.session_state.edits_applied_count is not None and st.session_state.edits_applied_count > 0):
            st.success(st.session_state.status_message)
        elif st.session_state.edits_suggested_count == 0 or \
             (st.session_state.edits_suggested_count is not None and st.session_state.edits_applied_count == 0):
            st.info(st.session_state.status_message)
        else: # Default or partial success
            st.info(st.session_state.status_message) # Or st.write

        if st.session_state.edits_suggested_count is not None and st.session_state.edits_applied_count is not None:
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="LLM Edits Suggested", value=st.session_state.edits_suggested_count)
            with col2:
                st.metric(label="Edits Successfully Applied", value=st.session_state.edits_applied_count)

    if st.session_state.error_message: # If there was an error during the last attempt
        st.error(st.session_state.error_message)

    if st.session_state.processed_file_url and st.session_state.processed_filename:
        st.markdown("---")
        try:
            file_response = requests.get(st.session_state.processed_file_url, stream=True, timeout=60)
            file_response.raise_for_status()
            file_bytes = file_response.content

            st.download_button(
                label=f"📥 Download {st.session_state.processed_filename}",
                data=file_bytes,
                file_name=st.session_state.processed_filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        except Exception as e:
            st.error(f"Could not fetch processed file for download: {e}. You can try downloading from this link: [{st.session_state.processed_filename}]({st.session_state.processed_file_url})")
            st.markdown(f"Alternatively, try to download directly: [{st.session_state.processed_filename}]({st.session_state.processed_file_url})")

    if st.session_state.log_content: # This is the processor log (ambiguities, skips etc.)
        st.markdown("---")
        st.subheader("📝 Processing Log")
        st.text_area("Processing Log Details", value=st.session_state.log_content, height=200, disabled=True, label_visibility="visible")

    # To display backend debug log in UI (if backend is modified to send it)
    # if show_debug_in_ui and st.session_state.debug_log_from_backend:
    #     st.markdown("---")
    #     st.subheader("🖥️ Server Debug Output")
    #     st.text_area("Server Debug Log", value=st.session_state.debug_log_from_backend, height=200, disabled=True, label_visibility="visible")