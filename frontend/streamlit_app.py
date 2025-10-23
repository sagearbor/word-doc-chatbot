import os
import requests
import streamlit as st

# Configuration for the FastAPI backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
PROCESS_ENDPOINT = f"{BACKEND_URL}/process-document/"
PROCESS_WITH_FALLBACK_ENDPOINT = f"{BACKEND_URL}/process-document-with-fallback/"
ANALYZE_FALLBACK_ENDPOINT = f"{BACKEND_URL}/analyze-fallback-requirements/"
DOWNLOAD_ENDPOINT_PREFIX = f"{BACKEND_URL}/download"
ANALYZE_ENDPOINT = f"{BACKEND_URL}/analyze-document/" # Endpoint for analysis

st.set_page_config(layout="wide", page_title="Word Document Editor")

st.title("📄 Word Document Tracked Changes Assistant")
st.markdown("""
Upload a Word document (.docx). You can:
1.  **Analyze existing tracked changes**: Get an AI-generated summary of the tracked changes already in the document.
2.  **Process new changes**: Provide instructions for new edits, which the AI will interpret and apply as tracked changes.
3.  **Use fallback document**: Upload a second document with guidance/requirements to help edit the main document.
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
if 'fallback_analysis_content' not in st.session_state: st.session_state.fallback_analysis_content = None
if 'use_fallback_mode' not in st.session_state: st.session_state.use_fallback_mode = False


with st.sidebar:
    st.header("⚙️ Options")
    uploaded_file = st.file_uploader("1. Upload your main .docx file", type=["docx"], key="file_uploader")
    
    # Fallback document option
    st.markdown("---")
    st.subheader("📋 Fallback Document (Optional)")
    use_fallback = st.checkbox("Use fallback document for guidance", value=st.session_state.use_fallback_mode,
                              help="Upload a second document that contains:\n"
                                   "• Tracked changes to apply to the main document (preferred), OR\n"
                                   "• Requirements/guidance text for AI to interpret\n\n"
                                   "If the fallback document has tracked changes, they will be extracted and applied directly!")
    
    fallback_file = None
    if use_fallback:
        st.session_state.use_fallback_mode = True
        fallback_file = st.file_uploader("Upload fallback .docx file", type=["docx"], key="fallback_uploader")
        
        if fallback_file:
            st.info(f"📄 Fallback document: {fallback_file.name}")
            st.markdown("""
            **How fallback documents work:**
            - ✨ **With tracked changes**: Changes are extracted and applied directly to your main document
            - 📝 **With requirements text**: AI interprets the requirements and generates appropriate edits
            - 🔄 **Mixed content**: Both tracked changes and requirements can be used together
            """)
            
            # Option to analyze fallback document
            if st.button("🔍 Analyze Fallback Requirements", disabled=st.session_state.processing, key="analyze_fallback_button"):
                st.session_state.processing = True
                st.session_state.fallback_analysis_content = None
                st.session_state.error_message = None
                
                with st.spinner("Analyzing fallback document requirements..."):
                    files = {"file": (fallback_file.name, fallback_file.getvalue(), fallback_file.type)}
                    form_data = {"context": "Analyzing fallback document for editing guidance"}
                    try:
                        response = requests.post(ANALYZE_FALLBACK_ENDPOINT, files=files, data=form_data, timeout=120)
                        response.raise_for_status()
                        result = response.json()
                        
                        if result.get("status") == "success":
                            st.session_state.fallback_analysis_content = {
                                "instructions": result.get("instructions", ""),
                                "requirements_count": result.get("requirements_count", 0),
                                "categorized_requirements": result.get("categorized_requirements", {})
                            }
                            st.success(f"✅ Found {result.get('requirements_count', 0)} requirements in fallback document!")
                        else:
                            st.session_state.error_message = f"Fallback analysis failed: {result}"
                            
                    except requests.exceptions.HTTPError as errh:
                        error_body = "Could not parse error response."
                        try: 
                            error_body = errh.response.json().get("detail", errh.response.text)
                        except ValueError: 
                            error_body = errh.response.text if errh.response.text else "HTTP Error with no details."
                        st.session_state.error_message = f"Fallback analysis failed (HTTP Error): {errh.response.status_code} - {error_body}"
                    except requests.exceptions.ConnectionError as errc:
                        st.session_state.error_message = f"Fallback analysis failed (Connection Error): {errc}\nIs the backend server running at {BACKEND_URL}?"
                    except requests.exceptions.Timeout:
                        st.session_state.error_message = "Fallback analysis failed (Timeout Error): The request took too long."
                    except Exception as e:
                        st.session_state.error_message = f"Fallback analysis failed (Unexpected Error): {str(e)}"
                    finally:
                        st.session_state.processing = False
    else:
        st.session_state.use_fallback_mode = False

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
    
    # Fallback processing options (only show when fallback is enabled)
    if use_fallback and fallback_file:
        st.subheader("📋 Fallback Processing Options")
        merge_strategy_options = {
            "Append": "append",
            "Prepend": "prepend", 
            "Priority (Fallback takes precedence)": "priority"
        }
        merge_strategy = st.selectbox(
            "Merge Strategy:",
            options=list(merge_strategy_options.keys()),
            index=0,
            help="How to combine your instructions with the fallback document requirements."
        )
        merge_strategy_payload = merge_strategy_options[merge_strategy]
    
    st.markdown("---")
    st.subheader("🤖 AI Processing Mode")
    
    # Fetch current LLM configuration
    llm_config = None
    try:
        config_response = requests.get(f"{BACKEND_URL}/llm-config/", timeout=5)
        if config_response.status_code == 200:
            llm_config = config_response.json()
    except:
        pass  # Silently handle errors - this is not critical
    
    if llm_config:
        current_mode = llm_config.get("current_mode", "Unknown")
        st.info(f"**Current Mode**: {current_mode}")
        
        # Extraction method selection
        extraction_options = {
            "🧠 LLM-Based (Recommended)": "llm",
            "📝 Regex-Based (Legacy)": "regex"
        }
        current_extraction = "llm" if llm_config.get("llm_extraction_enabled", False) else "regex"
        extraction_choice = st.selectbox(
            "📋 Requirement Extraction (Step 1):",
            options=list(extraction_options.keys()),
            index=0 if current_extraction == "llm" else 1,
            help="How to find requirements in fallback documents:\n• LLM: AI reads and understands document context intelligently\n• Regex: Uses hardcoded text patterns (limited to specific phrases)"
        )
        
        # Instruction method selection
        instruction_options = {
            "🧠 LLM-Based (Recommended)": "llm", 
            "📝 Hardcoded (Legacy)": "hardcoded"
        }
        current_instructions = "llm" if llm_config.get("llm_instructions_enabled", False) else "hardcoded"
        instruction_choice = st.selectbox(
            "✏️ Instruction Generation (Step 2):",
            options=list(instruction_options.keys()),
            index=0 if current_instructions == "llm" else 1,
            help="How to create 'Change X to Y' instructions:\n• LLM: AI creates smart instructions understanding context\n• Hardcoded: Uses fixed text replacement patterns (limited flexibility)"
        )
        
        # Update configuration button
        if st.button("🔄 Update AI Mode", help="Apply the selected AI processing configuration"):
            try:
                config_data = {
                    "extraction_method": extraction_options[extraction_choice],
                    "instruction_method": instruction_options[instruction_choice]
                }
                
                config_response = requests.post(f"{BACKEND_URL}/llm-config/", data=config_data, timeout=10)
                if config_response.status_code == 200:
                    result = config_response.json()
                    st.success(f"✅ Configuration updated! New mode: {result.get('new_mode', 'Unknown')}")
                    st.rerun()  # Refresh to show new config
                else:
                    st.error("❌ Failed to update configuration")
            except Exception as e:
                st.error(f"❌ Error updating configuration: {str(e)}")
    else:
        st.warning("⚠️ Could not fetch LLM configuration from backend")
    
    st.markdown("---") 
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
    instruction_label = "Describe the checks or changes you want the AI to make:"
    instruction_placeholder = "e.g., 'Change all instances of Mr. Smith to Ms. Jones. Update project deadline from 2024-01-01 to 2024-02-15.'"
    
    if use_fallback and fallback_file:
        instruction_label += " (Optional when using fallback document)"
        instruction_placeholder = "Optional: Add your custom instructions here. If left empty, only fallback document requirements will be applied."
    
    user_instructions = st.text_area(
        instruction_label,
        height=150, key="instructions_area",
        placeholder=instruction_placeholder
    )

    # Determine if processing should be enabled
    # Allow processing if: has main file AND (has instructions OR has fallback file)
    can_process = uploaded_file and (user_instructions.strip() or (use_fallback and fallback_file))
    
    if st.button("✨ Process Document with New Changes", type="primary", 
                  disabled=st.session_state.processing or not can_process, 
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

        # Determine if we're using fallback processing
        using_fallback = use_fallback and fallback_file
        endpoint = PROCESS_WITH_FALLBACK_ENDPOINT if using_fallback else PROCESS_ENDPOINT
        
        with st.spinner("Processing your document for new changes... This may take a moment."):
            files = {"input_file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            
            # Add fallback file if using fallback mode
            if using_fallback:
                files["fallback_file"] = (fallback_file.name, fallback_file.getvalue(), fallback_file.type)
                payload = {
                    "user_instructions": user_instructions, "author_name": author_name_llm,
                    "case_sensitive": case_sensitive_search, "add_comments": add_comments_to_changes,
                    "debug_mode": debug_mode_payload, "extended_debug_mode": extended_debug_mode_payload,
                    "merge_strategy": merge_strategy_payload
                }
            else:
                # Standard processing payload
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                payload = {
                    "instructions": user_instructions, "author_name": author_name_llm,
                    "case_sensitive": case_sensitive_search, "add_comments": add_comments_to_changes,
                    "debug_mode": debug_mode_payload, "extended_debug_mode": extended_debug_mode_payload
                }
            
            try:
                response = requests.post(endpoint, files=files, data=payload, timeout=300)
                response.raise_for_status()
                result = response.json()
                st.session_state.processed_filename = result.get("processed_filename")
                st.session_state.processed_file_url = f"{DOWNLOAD_ENDPOINT_PREFIX}/{st.session_state.processed_filename}" if st.session_state.processed_filename else None
                st.session_state.log_content = result.get("log_content", "No log content received.")
                st.session_state.status_message = result.get("status_message", "Processing finished.")
                st.session_state.edits_applied_count = result.get("edits_applied_count")
                st.session_state.edits_suggested_count = result.get("edits_suggested_count")
                st.session_state.debug_info = result.get("debug_info")
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

    # Display fallback analysis content if available
    if st.session_state.fallback_analysis_content and not st.session_state.processing:
        st.markdown("---")
        st.markdown("**📋 Fallback Document Analysis:**")
        
        fallback_data = st.session_state.fallback_analysis_content
        requirements_count = fallback_data.get("requirements_count", 0)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Requirements Found", requirements_count)
        with col2:
            categorized_reqs = fallback_data.get("categorized_requirements", {})
            st.metric("Categories", len(categorized_reqs))
        
        if fallback_data.get("instructions"):
            with st.expander("📝 Generated Instructions from Fallback Document", expanded=False):
                st.text_area("Instructions:", value=fallback_data["instructions"], height=150, disabled=True, label_visibility="collapsed")
        
        if categorized_reqs:
            with st.expander("🔍 Categorized Requirements Preview", expanded=False):
                for category, requirements in list(categorized_reqs.items())[:3]:  # Show first 3 categories
                    st.markdown(f"**{category.replace('_', ' ').title()}:**")
                    for req in requirements[:2]:  # Show first 2 requirements per category
                        st.markdown(f"- {req.get('text', 'N/A')[:100]}{'...' if len(req.get('text', '')) > 100 else ''}")
                    if len(requirements) > 2:
                        st.markdown(f"  *(+{len(requirements) - 2} more requirements)*")
                    st.markdown("")
                
                if len(categorized_reqs) > 3:
                    st.markdown(f"*+{len(categorized_reqs) - 3} more categories*")
        
        st.info("💡 These requirements will be automatically combined with your instructions when processing the document.")

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
        
        # Show debug information if available
        if hasattr(st.session_state, 'debug_info') and st.session_state.debug_info:
            debug_info = st.session_state.debug_info
            
            # User-friendly debug summary (always shown when debug is enabled)
            if "user_friendly_summary" in debug_info:
                with st.expander("🔍 Processing Summary", expanded=True):
                    summary = debug_info["user_friendly_summary"]
                    
                    st.markdown("**What happened:**")
                    st.markdown(f"• {summary.get('requirements_found', 'Requirements processing')}")
                    st.markdown(f"• {summary.get('llm_processing', 'LLM processing')}")
                    st.markdown(f"• {summary.get('document_processing', 'Document processing')}")
                    
                    if summary.get("potential_issues"):
                        st.markdown("**Potential Issues:**")
                        for issue in summary["potential_issues"]:
                            st.markdown(f"• {issue}")
            
            # Extended technical details (only shown in extended mode)
            if debug_info.get("extended_debug_enabled") and "extended_details" in debug_info:
                with st.expander("🔧 Extended Debug Details", expanded=False):
                    extended = debug_info["extended_details"]
                    
                    st.markdown("**Processing Method:**")
                    st.code(extended.get("processing_method", "Unknown"))
                    
                    st.markdown("**Instruction Merging:**")
                    st.text(extended.get("instruction_merging", "N/A"))
                    
                    # Show fallback document analysis if available
                    if isinstance(extended.get("fallback_document_analysis"), dict):
                        fallback_analysis = extended["fallback_document_analysis"]
                        
                        st.markdown("**Fallback Document Analysis:**")
                        
                        if "error" in fallback_analysis:
                            st.error(f"Analysis error: {fallback_analysis['error']}")
                        else:
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Requirements Found", fallback_analysis.get("fallback_requirements_count", 0))
                            with col2:
                                req_types = fallback_analysis.get("requirement_types", [])
                                st.metric("Requirement Types", len(req_types))
                            
                            if req_types:
                                st.markdown(f"**Requirement types detected:** {', '.join(req_types)}")
                            
                            sample_reqs = fallback_analysis.get("sample_requirements", [])
                            if sample_reqs:
                                st.markdown("**Sample requirements from fallback document:**")
                                for i, req in enumerate(sample_reqs, 1):
                                    st.markdown(f"{i}. {req}")
                        
                        st.markdown("---")
                    
                    if "edit_details" in extended and extended["edit_details"]:
                        st.markdown("**Edit Details:**")
                        for edit in extended["edit_details"]:
                            status_icon = "✅" if edit.get("applied_successfully") else "❌"
                            st.markdown(f"{status_icon} **Edit {edit.get('edit_number', 'N/A')}:**")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.text_area(
                                    f"Original text (Edit {edit.get('edit_number', 'N/A')}):",
                                    edit.get("old_text", "N/A")[:200],
                                    height=75,
                                    disabled=True,
                                    key=f"old_text_{edit.get('edit_number', 'N/A')}"
                                )
                            with col2:
                                st.text_area(
                                    f"New text (Edit {edit.get('edit_number', 'N/A')}):",
                                    edit.get("new_text", "N/A")[:200],
                                    height=75,
                                    disabled=True,
                                    key=f"new_text_{edit.get('edit_number', 'N/A')}"
                                )
                            
                            if edit.get("reason"):
                                st.markdown(f"**Reason:** {edit['reason']}")
                            
                            st.markdown("---")
            
            # Technical JSON (always available for developers)
            with st.expander("🔧 Technical Debug Data (JSON)", expanded=False):
                st.json(debug_info)
        
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
        # Check if there are issues/rejected edits in the log
        has_issues = "Type:" in st.session_state.log_content and "Issue:" in st.session_state.log_content

        if has_issues:
            # Show warning with expander for rejected/skipped edits
            with st.expander("⚠️ Processing Log (Why Some Edits Were Skipped)", expanded=False):
                st.markdown("**Common reasons edits are skipped:**")
                st.markdown("- `context not found` - The text wasn't found in the document")
                st.markdown("- `ambiguous` - Multiple matches found, needs manual review")
                st.markdown("- `boundary rule skip` - Text doesn't have proper word boundaries")
                st.text_area("Full Log Details:", value=st.session_state.log_content, height=200, disabled=True, label_visibility="collapsed")
        else:
            # Just show a simple success message
            with st.expander("✅ Processing Log", expanded=False):
                st.text_area("Log Details:", value=st.session_state.log_content, height=150, disabled=True, label_visibility="collapsed")
        # st.session_state.log_content = None # Optionally clear

# Placeholder for no action yet
if not st.session_state.analysis_content and not st.session_state.status_message and not st.session_state.error_message and not st.session_state.processing:
    if uploaded_file:
        st.info("Upload a document and choose an action from the sidebar.")
    else:
        st.info("Upload a document using the sidebar to get started.")