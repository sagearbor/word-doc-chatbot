import os
import requests
import streamlit as st

# Configuration for the FastAPI backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
PROCESS_ENDPOINT = f"{BACKEND_URL}/process-document/"
DOWNLOAD_ENDPOINT_PREFIX = f"{BACKEND_URL}/download"
ANALYZE_ENDPOINT = f"{BACKEND_URL}/analyze-document/" # Endpoint for analysis

st.set_page_config(layout="wide", page_title="Word Document Editor")

st.title("📄 Word Document Tracked Changes Assistant")
st.markdown("""
Upload a Word document (.docx). You can either:
1.  **Analyze existing tracked changes**: Get an AI-generated summary of the tracked changes already in the document.
2.  **Process new changes**: Provide instructions for new edits, which the AI will interpret and apply as tracked changes.
You can then download the modified document.
""")

# --- Session State Initialization ---
# ... (keep existing session state initializations) ...
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

    st.markdown("---") # Separator
    st.subheader("A. Analyze Existing Changes")
    analysis_mode_options = {
        "Summarize Extracted Changes (Concise Input to AI)": "summary",
        "Summarize from Raw Document XML (Verbose Input to AI)": "raw_xml"
    }
    selected_analysis_mode_display = st.selectbox(
        "Analysis Method:",
        options=list(analysis_mode_options.keys()),
        index=0, # Default to summary (Concise)
        help="Choose how the document's existing tracked changes are analyzed. 'Concise' sends a pre-processed list of changes. 'Verbose' sends the raw internal XML (can be slow or fail for large/complex docs, but might give more context)."
    )
    analysis_mode_payload = analysis_mode_options[selected_analysis_mode_display]

    if st.button("🔍 Analyze Existing Tracked Changes", disabled=st.session_state.processing or not uploaded_file, key="analyze_button"):
        st.session_state.processing = True
        st.session_state.analysis_content = None 
        st.session_state.error_message = None
        # Clear other potentially irrelevant messages from process document
        st.session_state.processed_file_url = None
        st.session_state.log_content = None
        st.session_state.status_message = None


        with st.spinner(f"Analyzing with '{selected_analysis_mode_display}' method... This may take a moment."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            # Pass analysis_mode as form data
            form_data = {"analysis_mode": analysis_mode_payload}
            try:
                # Timeout can be crucial here, especially for raw_xml mode
                response = requests.post(ANALYZE_ENDPOINT, files=files, data=form_data, timeout=120) # Increased timeout
                response.raise_for_status() # Will raise an HTTPError for bad responses (4xx or 5xx)
                
                analysis_result = response.json().get("analysis", "No analysis content returned.")
                
                # Check for specific error markers from backend
                if analysis_result.startswith("Error_"):
                    st.session_state.error_message = f"Analysis Error: {analysis_result.replace('Error_Internal:', '').replace('Error_AI:', '').replace('Error_Input:', '').replace('Error_Server:', '')}"
                    st.session_state.analysis_content = None # Clear any partial content
                else:
                    st.session_state.analysis_content = analysis_result
                    st.success("Analysis of existing changes complete!")

            except requests.exceptions.HTTPError as errh:
                error_body = "Could not parse error response."
                try: error_body = errh.response.json().get("detail", errh.response.text)
                except ValueError: error_body = errh.response.text if errh.response.text else "Http Error with no details."
                st.session_state.error_message = f"Analysis failed (HTTP Error): {errh.response.status_code} - {error_body}"
            except requests.exceptions.ConnectionError as errc:
                st.session_state.error_message = f"Analysis failed (Connection Error): {errc}\nIs the backend server running at {BACKEND_URL}?"
            except requests.exceptions.Timeout:
                st.session_state.error_message = "Analysis failed (Timeout Error): The request took too long. The 'Raw XML' mode can be slow for large files."
            except Exception as e:
                st.session_state.error_message = f"Analysis failed (Unexpected Error): {str(e)}"
            finally:
                st.session_state.processing = False
                # st.rerun() # Rerun to update UI based on new session state
                # No, don't rerun here yet, let the main page display logic handle it.

    st.markdown("---") # Separator
    st.subheader("B. Process New Changes")
    author_name_llm = st.text_input(
        "Name for AI's new changes:", value="AI Reviewer",
        help="This name will be used as the author for new tracked changes made by the AI based on your instructions below."
    )
    case_sensitive_search = st.checkbox("Case-sensitive search for new changes", value=True)
    add_comments_to_changes = st.checkbox("Add AI comments to new changes", value=True)
    
    st.subheader("Debugging (for new changes processing)")
    debug_level_options = {
        "Off": ("off", "No server-side debugging."),
        "Standard Debugging": ("standard", "Logs detailed processing steps."),
        "Extended Debugging": ("extended", "Logs very verbose details (implies Standard).")
    }
    debug_level_choice = st.selectbox(
        "Server Debugging Level:", options=list(debug_level_options.keys()), index=0,
        format_func=lambda x: f"{x} - {debug_level_options[x][1]}"
    )
    debug_mode_payload = False
    extended_debug_mode_payload = False
    if debug_level_options[debug_level_choice][0] == "standard": debug_mode_payload = True
    elif debug_level_options[debug_level_choice][0] == "extended":
        debug_mode_payload = True
        extended_debug_mode_payload = True
    
# --- Main Page Content ---
cols_main = st.columns([0.6, 0.4]) # Adjust column proportions as needed

with cols_main[0]: # Left column for instructions and processing
    st.header("✍️ Instruct AI for New Changes")
    user_instructions = st.text_area(
        "Describe the checks or changes you want the AI to make:",
        height=150, key="instructions_area",
        placeholder="e.g., 'Change all instances of Mr. Smith to Ms. Jones. Update project deadline from 2024-01-01 to 2024-02-15.'"
    )

    if st.button("✨ Process Document with New Changes", type="primary", 
                  disabled=st.session_state.processing or not uploaded_file or not user_instructions, 
                  key="process_button"):
        st.session_state.processing = True
        # Clear previous results from both analysis and processing
        st.session_state.processed_file_url = None
        st.session_state.processed_filename = None
        st.session_state.log_content = None
        st.session_state.error_message = None
        st.session_state.status_message = None
        st.session_state.edits_applied_count = None
        st.session_state.edits_suggested_count = None
        st.session_state.analysis_content = None # Clear analysis content too
        st.session_state.debug_log_from_backend = None

        with st.spinner("Processing your document for new changes... This may take a moment."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            payload = {
                "instructions": user_instructions, "author_name": author_name_llm,
                "case_sensitive": case_sensitive_search, "add_comments": add_comments_to_changes,
                "debug_mode": debug_mode_payload, "extended_debug_mode": extended_debug_mode_payload
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
                # st.success(st.session_state.status_message) # Success message will be shown in main display area
            except requests.exceptions.HTTPError as errh:
                error_body = "Could not parse error."
                try: error_body = errh.response.json().get("detail", errh.response.text)
                except ValueError: error_body = errh.response.text if errh.response.text else "Http Error with no details."
                st.session_state.error_message = f"Processing failed (Http Error): {errh.response.status_code} - {error_body}"
            except requests.exceptions.ConnectionError as errc:
                st.session_state.error_message = f"Processing failed (Connection Error): {errc}\nIs the backend server running at {BACKEND_URL}?"
            except requests.exceptions.Timeout:
                st.session_state.error_message = "Processing failed (Timeout Error): The request took too long."
            except Exception as e:
                st.session_state.error_message = f"Processing failed (Unexpected Error): {str(e)}"
            finally:
                st.session_state.processing = False
                st.rerun() # Rerun to update UI

with cols_main[1]: # Right column for displaying results/analysis
    st.header("🔎 Analysis & Results")

    # Display error messages first if any
    if st.session_state.error_message and not st.session_state.processing:
        st.error(st.session_state.error_message)
        # st.session_state.error_message = None # Clear after displaying once if desired

    # Display analysis content if available
    if st.session_state.analysis_content and not st.session_state.processing:
        st.markdown("---")
        st.markdown("**AI Summary of Existing Tracked Changes:**")
        st.text_area("Analysis Details:", value=st.session_state.analysis_content, height=200, disabled=True, label_visibility="collapsed")
        st.info("This summary is based on the tracked changes found in the uploaded document using the selected analysis method.")
        # st.session_state.analysis_content = None # Optionally clear after displaying

    # Display processing status and results if available
    if st.session_state.status_message and not st.session_state.processing:
        st.markdown("---")
        st.markdown("**New Changes Processing Status:**")
        if "success" in st.session_state.status_message.lower() or \
           (st.session_state.edits_applied_count is not None and st.session_state.edits_applied_count > 0):
            st.success(st.session_state.status_message)
        elif st.session_state.edits_suggested_count == 0 or \
             (st.session_state.edits_suggested_count is not None and st.session_state.edits_applied_count == 0 and "Processing complete" in st.session_state.status_message): # Avoid info for critical fail
            st.info(st.session_state.status_message)
        else: 
            st.info(st.session_state.status_message)

        if st.session_state.edits_suggested_count is not None and st.session_state.edits_applied_count is not None:
            metric_col1, metric_col2 = st.columns(2)
            with metric_col1:
                st.metric(label="AI Edits Suggested", value=st.session_state.edits_suggested_count)
            with metric_col2:
                st.metric(label="Edits Successfully Applied", value=st.session_state.edits_applied_count)
        # st.session_state.status_message = None # Optionally clear

    if st.session_state.processed_file_url and st.session_state.processed_filename and not st.session_state.processing:
        st.markdown("---")
        try:
            # Fetch the file content for the download button
            # This is done when results are displayed to ensure file is ready
            file_response = requests.get(st.session_state.processed_file_url, stream=True, timeout=60)
            file_response.raise_for_status()
            file_bytes = file_response.content

            st.download_button(
                label=f"📥 Download {st.session_state.processed_filename}",
                data=file_bytes,
                file_name=st.session_state.processed_filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        except Exception as e_download:
            st.error(f"Could not prepare processed file for download: {e_download}. You can try the direct link if available, or reprocess.")
            st.markdown(f"Direct link (may or may not work if file was cleaned up): [{st.session_state.processed_filename}]({st.session_state.processed_file_url})")
        # st.session_state.processed_file_url = None # Optionally clear

    if st.session_state.log_content and not st.session_state.processing:
        st.markdown("---")
        st.subheader("📝 New Changes Processing Log")
        st.text_area("Log Details:", value=st.session_state.log_content, height=200, disabled=True, label_visibility="collapsed")
        # st.session_state.log_content = None # Optionally clear

# Placeholder for no action yet
if not st.session_state.analysis_content and not st.session_state.status_message and not st.session_state.error_message and not st.session_state.processing:
    if uploaded_file:
        st.info("Upload a document and choose an action from the sidebar.")
    else:
        st.info("Upload a document using the sidebar to get started.")