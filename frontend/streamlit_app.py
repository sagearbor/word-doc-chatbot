import streamlit as st
import requests
import os
import time # For polling if needed, or just for unique keys

# Configuration for the FastAPI backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
PROCESS_ENDPOINT = f"{BACKEND_URL}/process-document/"
DOWNLOAD_ENDPOINT_PREFIX = f"{BACKEND_URL}/download" # No trailing slash
ANALYZE_ENDPOINT = f"{BACKEND_URL}/analyze-document/"

st.set_page_config(layout="wide", page_title="Word Document Editor")

st.title("📄 Word Document Tracked Changes Assistant")
st.markdown("""
Upload a Word document (.docx) and provide instructions for the changes you want.
The AI will interpret your instructions, and the system will apply them as tracked changes.
You can then download the modified document.
""")

# --- Session State Initialization ---
if 'processed_file_url' not in st.session_state:
    st.session_state.processed_file_url = None
if 'processed_filename' not in st.session_state:
    st.session_state.processed_filename = None
if 'log_content' not in st.session_state:
    st.session_state.log_content = None
if 'error_message' not in st.session_state:
    st.session_state.error_message = None
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'analysis_content' not in st.session_state:
    st.session_state.analysis_content = None


with st.sidebar:
    st.header("⚙️ Options")
    uploaded_file = st.file_uploader("1. Upload your .docx file", type=["docx"], key="file_uploader")

    if st.button("🔍 Analyze Document for Suggestions", disabled=st.session_state.processing):
        if uploaded_file is not None:
            st.session_state.processing = True
            with st.spinner("Analyzing document with LLM..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                try:
                    response = requests.post(ANALYZE_ENDPOINT, files=files, timeout=300)
                    response.raise_for_status()
                    analysis_result = response.json().get("analysis", "No analysis returned.")
                    st.session_state.analysis_content = analysis_result
                    st.session_state.processed_file_url = None
                    st.session_state.processed_filename = None
                    st.session_state.log_content = None
                    st.success("Analysis complete. See suggestions below.")
                except Exception as e:
                    st.session_state.error_message = f"Analysis failed: {e}"
                    st.error(st.session_state.error_message)
                finally:
                    st.session_state.processing = False
                    st.experimental_rerun()
        else:
            st.warning("Please upload a .docx file for analysis.")
    
    st.subheader("Author for Changes (Optional)")
    author_name_llm = st.text_input("Name to appear for LLM's changes:", value="AI Reviewer", help="This name will be used as the author for the tracked changes made by the LLM.")

    st.subheader("Search Settings")
    case_sensitive_search = st.checkbox("Case-sensitive search for text to change", value=True, help="If checked, 'Text' and 'text' are treated as different. If unchecked, they are treated the same.")
    
    st.subheader("Tracked Changes Settings")
    add_comments_to_changes = st.checkbox("Add comments to changes", value=True, help="If checked, the LLM's reason for change will be added as a comment to the tracked change.")


user_instructions = st.text_area(
    "2. Describe the checks or changes you want (e.g., 'Ensure all deadlines are after May 5th, 2024. Correct spelling of Contoso Ltd to Contoso Inc.')",
    height=150,
    key="instructions_area"
)

if st.session_state.analysis_content:
    st.markdown("**LLM Suggested Improvements:**")
    st.text_area("Suggestions", value=st.session_state.analysis_content, height=200, disabled=True)

if st.button("✨ Process Document", type="primary", disabled=st.session_state.processing):
    if uploaded_file is not None and user_instructions:
        st.session_state.processing = True
        st.session_state.processed_file_url = None
        st.session_state.processed_filename = None
        st.session_state.log_content = None
        st.session_state.error_message = None
        st.session_state.analysis_content = None
        
        with st.spinner("Processing your document... This may take a moment. Please wait."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            payload = {
                "instructions": user_instructions,
                "author_name": author_name_llm,
                "case_sensitive": case_sensitive_search,
                "add_comments": add_comments_to_changes
            }
            
            try:
                response = requests.post(PROCESS_ENDPOINT, files=files, data=payload, timeout=300) # 5 min timeout
                response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
                
                result = response.json()
                st.session_state.processed_filename = result.get("processed_filename")
                st.session_state.processed_file_url = f"{DOWNLOAD_ENDPOINT_PREFIX}/{st.session_state.processed_filename}" if st.session_state.processed_filename else None
                st.session_state.log_content = result.get("log_content", "No log content received.")
                
                st.success("Document processing complete!")

            except requests.exceptions.HTTPError as errh:
                st.session_state.error_message = f"Http Error: {errh.response.status_code} {errh.response.reason}"
                try:
                    error_detail = errh.response.json().get("detail", "No additional details.")
                    st.session_state.error_message += f"\nDetails: {error_detail}"
                except ValueError: # If response is not JSON
                    st.session_state.error_message += f"\nResponse: {errh.response.text}"
                st.error(st.session_state.error_message)
            except requests.exceptions.ConnectionError as errc:
                st.session_state.error_message = f"Error Connecting: {errc}\nIs the backend server running at {BACKEND_URL}?"
                st.error(st.session_state.error_message)
            except requests.exceptions.Timeout as errt:
                st.session_state.error_message = f"Timeout Error: {errt}\nThe request took too long to complete."
                st.error(st.session_state.error_message)
            except requests.exceptions.RequestException as err:
                st.session_state.error_message = f"Oops, something went wrong: {err}"
                st.error(st.session_state.error_message)
            except Exception as e:
                st.session_state.error_message = f"An unexpected error occurred: {e}"
                st.error(st.session_state.error_message)
            finally:
                st.session_state.processing = False
                # Force a rerun to update UI elements based on new session state
                st.experimental_rerun()


    elif not uploaded_file:
        st.warning("Please upload a .docx file.")
    elif not user_instructions:
        st.warning("Please provide instructions for the changes.")

# --- Display Results ---
if st.session_state.error_message and not st.session_state.processing:
    st.error(f"Last processing attempt failed: {st.session_state.error_message}")

if st.session_state.processed_file_url and st.session_state.processed_filename and not st.session_state.processing:
    st.markdown("---")
    st.subheader("✅ Processed Document Ready!")
    
    # To offer a direct download button, we need the actual file bytes.
    # The URL points to the FastAPI server. We can fetch it and then provide a download button.
    try:
        # Fetch the processed file from the backend for download
        # This adds an extra request but ensures the download is initiated from Streamlit
        # and gives more control over the filename.
        file_response = requests.get(st.session_state.processed_file_url, stream=True, timeout=60)
        file_response.raise_for_status()
        file_bytes = file_response.content
        
        st.download_button(
            label=f"📥 Download {st.session_state.processed_filename}",
            data=file_bytes,
            file_name=st.session_state.processed_filename, # User sees this name
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        st.error(f"Could not fetch processed file for download: {e}. You can try downloading from this link: [{st.session_state.processed_filename}]({st.session_state.processed_file_url})")
        # Provide a direct link as a fallback
        st.markdown(f"Alternatively, try to download directly: [{st.session_state.processed_filename}]({st.session_state.processed_file_url})")


if st.session_state.log_content and not st.session_state.processing:
    st.markdown("---")
    st.subheader("📝 Processing Log")
    with st.expander("View Log Details", expanded=False):
        st.text_area("Log:", value=st.session_state.log_content, height=300, disabled=True, key="log_display_area")

st.markdown("---")
st.caption("Developed with Streamlit, FastAPI, and OpenAI.")
