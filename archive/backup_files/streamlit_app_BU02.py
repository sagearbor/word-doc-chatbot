import os
import requests
import streamlit as st

# Configuration for the FastAPI backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
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


with st.sidebar:
    st.header("⚙️ Options")
    uploaded_file = st.file_uploader("1. Upload your .docx file", type=["docx"], key="file_uploader")

    if st.button("🔍 Analyze Document for Suggestions", disabled=st.session_state.processing or not uploaded_file):
        st.session_state.processing = True
        st.session_state.analysis_content = None # Clear previous analysis
        st.session_state.error_message = None    # Clear previous errors
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
                st.rerun() # Rerun to update UI with analysis or error

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
    debug_mode_st = st.checkbox("Enable Debug Mode", value=False, help="Logs detailed processing steps to the server console.")
    extended_debug_mode_st = st.checkbox("Enable Extended Debug Mode", value=False, help="Logs very verbose details, including full contexts.")


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
    # st.session_state.analysis_content = None # Keep analysis if user wants to refer to it

    with st.spinner("Processing your document... This may take a moment. Please wait."):
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        payload = {
            "instructions": user_instructions,
            "author_name": author_name_llm,
            "case_sensitive": case_sensitive_search,
            "add_comments": add_comments_to_changes,
            "debug_mode": debug_mode_st,                   # Pass debug flag
            "extended_debug_mode": extended_debug_mode_st  # Pass extended debug flag
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
            
            # Display success message immediately
            st.success(st.session_state.status_message)
            if st.session_state.edits_suggested_count is not None and st.session_state.edits_applied_count is not None:
                st.metric(label="LLM Edits Suggested", value=st.session_state.edits_suggested_count)
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
            st.rerun() # Rerun to update UI elements based on new session state

# --- Display Results Area (after processing attempt) ---
if not st.session_state.processing: # Only show this section if not currently processing
    if st.session_state.status_message: # General status from backend
        # This is now shown above, but can be enhanced here if needed
        pass 

    if st.session_state.error_message: # If there was an error during the last attempt
        st.error(st.session_state.error_message)

    if st.session_state.processed_file_url and st.session_state.processed_filename:
        st.markdown("---")
        # st.subheader("✅ Processed Document Ready!") # Status message now covers this

        try:
            # Fetch the processed file from the backend for download button
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

    if st.session_state.log_content:
        st.markdown("---")
        st.subheader("📝 Processing Log")
        st.text_area("", value=st.session_state.log_content, height=200, disabled=True, label_visibility="collapsed")

# Removed the secondary chat-like interface at the bottom to simplify the UI to the main form-based interaction.
# If you want to re-enable it, ensure its session state ('messages') and widgets are correctly managed
# and do not conflict with the main form's session state for file processing.