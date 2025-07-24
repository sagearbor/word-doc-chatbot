import os
import requests
import streamlit as st
import json
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# Configuration for the FastAPI backend URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

# API Endpoints
PROCESS_ENDPOINT = f"{BACKEND_URL}/process-document/"
DOWNLOAD_ENDPOINT_PREFIX = f"{BACKEND_URL}/download"
ANALYZE_ENDPOINT = f"{BACKEND_URL}/analyze-document/"

# New Phase 2.2/4.1 Endpoints
UPLOAD_FALLBACK_ENDPOINT = f"{BACKEND_URL}/upload-fallback-document/"
ANALYZE_REQUIREMENTS_ENDPOINT = f"{BACKEND_URL}/analyze-fallback-requirements/"
PROCESS_WITH_FALLBACK_ENDPOINT = f"{BACKEND_URL}/process-document-with-fallback/"
ANALYZE_MERGE_ENDPOINT = f"{BACKEND_URL}/analyze-merge/"
LEGAL_WORKFLOW_ENDPOINT = f"{BACKEND_URL}/process-legal-document/"

st.set_page_config(
    layout="wide", 
    page_title="Legal Document Processor - Phase 3",
    page_icon="⚖️"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 18px;
        padding: 10px 20px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .workflow-stage {
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
    }
    .stage-completed {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
    }
    .stage-failed {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
    }
    .stage-pending {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚖️ Legal Document Processor - Advanced Workflow")
st.markdown("""
### Enhanced Document Processing with Fallback Requirements
This application now supports **Phase 4.1 Complete Legal Workflow** with:
- 📋 Fallback document requirements extraction
- 🔄 Intelligent instruction merging (Phase 2.2)
- 📊 Legal coherence validation
- 🎯 End-to-end workflow orchestration
""")

# Initialize session state
if 'workflow_mode' not in st.session_state:
    st.session_state.workflow_mode = "simple"
if 'processed_file_url' not in st.session_state:
    st.session_state.processed_file_url = None
if 'workflow_result' not in st.session_state:
    st.session_state.workflow_result = None
if 'requirements_data' not in st.session_state:
    st.session_state.requirements_data = None
if 'processing' not in st.session_state:
    st.session_state.processing = False

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Workflow mode selection
    workflow_mode = st.radio(
        "Select Workflow Mode:",
        ["Simple (Original)", "Enhanced (With Fallback)", "Complete Legal Workflow (Phase 4.1)"],
        index=0,
        help="Choose processing mode based on your needs"
    )
    
    if workflow_mode == "Simple (Original)":
        st.session_state.workflow_mode = "simple"
    elif workflow_mode == "Enhanced (With Fallback)":
        st.session_state.workflow_mode = "enhanced"
    else:
        st.session_state.workflow_mode = "complete"
    
    st.markdown("---")
    
    # File uploads
    st.subheader("📄 Document Upload")
    uploaded_file = st.file_uploader(
        "Upload Input Document (.docx)",
        type=["docx"],
        key="input_doc"
    )
    
    fallback_file = None
    if st.session_state.workflow_mode in ["enhanced", "complete"]:
        fallback_file = st.file_uploader(
            "Upload Fallback Document (.docx)",
            type=["docx"],
            key="fallback_doc",
            help="Document containing standard requirements to be applied"
        )
    
    st.markdown("---")
    
    # Processing options
    st.subheader("🔧 Processing Options")
    author_name = st.text_input(
        "Author Name for Tracked Changes",
        value="Legal AI Assistant",
        help="Name to appear in tracked changes"
    )
    
    if st.session_state.workflow_mode == "enhanced":
        merge_strategy = st.selectbox(
            "Merge Strategy",
            ["append", "prepend", "priority"],
            help="How to combine fallback requirements with user instructions"
        )
    
    if st.session_state.workflow_mode == "complete":
        col1, col2 = st.columns(2)
        with col1:
            enable_audit = st.checkbox("Enable Audit Logging", value=True)
            enable_backup = st.checkbox("Enable Backup", value=True)
        with col2:
            enable_validation = st.checkbox("Enable Validation", value=True)
            debug_mode = st.checkbox("Debug Mode", value=False)
    
    # Advanced settings expander
    with st.expander("🎛️ Advanced Settings"):
        case_sensitive = st.checkbox("Case Sensitive Matching", value=True)
        add_comments = st.checkbox("Add Comments to Changes", value=True)
        if st.session_state.workflow_mode == "complete":
            performance_mode = st.selectbox(
                "Performance Mode",
                ["balanced", "fast", "thorough"],
                help="Optimization for processing speed vs thoroughness"
            )

# Main content area with tabs
if st.session_state.workflow_mode == "simple":
    # Original simple interface
    tab1, tab2 = st.tabs(["📝 Process Document", "📊 Analysis"])
else:
    # Enhanced interface with more tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Process Document", 
        "📋 Requirements Analysis",
        "🔄 Workflow Progress",
        "📊 Results & Metrics",
        "📚 Help & Guide"
    ])

# Tab 1: Process Document
with tab1:
    st.header("Document Processing")
    
    # User instructions
    user_instructions = st.text_area(
        "Enter your instructions for document modifications:",
        height=150,
        placeholder="Example: Please update all payment terms to NET 45 days. Add GDPR compliance requirements to section 3.",
        help="Describe the changes you want to make to the document"
    )
    
    # Process button
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.session_state.workflow_mode == "simple":
            process_btn = st.button(
                "🚀 Process Document",
                disabled=st.session_state.processing or not uploaded_file,
                type="primary",
                use_container_width=True
            )
        elif st.session_state.workflow_mode == "enhanced":
            process_btn = st.button(
                "🚀 Process with Fallback Requirements",
                disabled=st.session_state.processing or not uploaded_file or not fallback_file,
                type="primary",
                use_container_width=True
            )
        else:  # complete workflow
            process_btn = st.button(
                "🚀 Run Complete Legal Workflow",
                disabled=st.session_state.processing or not uploaded_file,
                type="primary",
                use_container_width=True
            )
    
    # Process document when button clicked
    if process_btn:
        st.session_state.processing = True
        st.session_state.workflow_result = None
        
        with st.spinner("Processing document... This may take a moment."):
            try:
                if st.session_state.workflow_mode == "simple":
                    # Original simple processing
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    data = {
                        "user_instructions": user_instructions,
                        "author_name": author_name,
                        "case_sensitive": case_sensitive,
                        "add_comments": add_comments
                    }
                    response = requests.post(PROCESS_ENDPOINT, files=files, data=data, timeout=180)
                    
                elif st.session_state.workflow_mode == "enhanced":
                    # Enhanced processing with fallback
                    files = {
                        "input_file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type),
                        "fallback_file": (fallback_file.name, fallback_file.getvalue(), fallback_file.type)
                    }
                    data = {
                        "user_instructions": user_instructions,
                        "author_name": author_name,
                        "case_sensitive": case_sensitive,
                        "add_comments": add_comments,
                        "merge_strategy": merge_strategy
                    }
                    response = requests.post(PROCESS_WITH_FALLBACK_ENDPOINT, files=files, data=data, timeout=300)
                    
                else:  # complete workflow
                    # Phase 4.1 Complete Legal Workflow
                    files = {"input_file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    if fallback_file:
                        files["fallback_file"] = (fallback_file.name, fallback_file.getvalue(), fallback_file.type)
                    
                    data = {
                        "user_instructions": user_instructions,
                        "author_name": author_name,
                        "enable_audit_logging": enable_audit,
                        "enable_backup": enable_backup,
                        "enable_validation": enable_validation
                    }
                    response = requests.post(LEGAL_WORKFLOW_ENDPOINT, files=files, data=data, timeout=600)
                
                response.raise_for_status()
                result = response.json()
                st.session_state.workflow_result = result
                st.session_state.processed_file_url = result.get("download_url")
                st.success("✅ Document processed successfully!")
                
            except requests.exceptions.HTTPError as e:
                st.error(f"Processing failed: {e}")
                if e.response:
                    try:
                        error_detail = e.response.json().get("detail", "Unknown error")
                        st.error(f"Details: {error_detail}")
                    except:
                        st.error(f"Response: {e.response.text}")
            except Exception as e:
                st.error(f"Unexpected error: {str(e)}")
            finally:
                st.session_state.processing = False
    
    # Display results if available
    if st.session_state.workflow_result:
        st.markdown("---")
        st.subheader("📄 Processing Results")
        
        result = st.session_state.workflow_result
        
        # Status message
        st.info(result.get("status_message", "Processing complete"))
        
        # Download button
        if st.session_state.processed_file_url:
            download_url = f"{BACKEND_URL}{st.session_state.processed_file_url}"
            st.markdown(f"### [📥 Download Processed Document]({download_url})")
        
        # Basic metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Edits Applied", result.get("edits_applied", 0))
        with col2:
            st.metric("Edits Suggested", result.get("edits_suggested", 0))
        with col3:
            st.metric("Issues", result.get("issues_count", 0))
        with col4:
            if result.get("legal_coherence_score") is not None:
                score = result["legal_coherence_score"]
                st.metric("Legal Coherence", f"{score:.2f}")
        
        # Log content
        if result.get("log_content"):
            with st.expander("📜 Processing Log"):
                st.text(result["log_content"])

# Tab 2: Requirements Analysis (only for enhanced/complete modes)
if st.session_state.workflow_mode != "simple":
    with tab2:
        st.header("📋 Fallback Requirements Analysis")
        
        if fallback_file:
            if st.button("🔍 Analyze Fallback Requirements"):
                with st.spinner("Analyzing fallback document..."):
                    try:
                        files = {"file": (fallback_file.name, fallback_file.getvalue(), fallback_file.type)}
                        data = {"context": f"Processing for {uploaded_file.name if uploaded_file else 'document'}"}
                        
                        response = requests.post(ANALYZE_REQUIREMENTS_ENDPOINT, files=files, data=data, timeout=120)
                        response.raise_for_status()
                        
                        req_data = response.json()
                        st.session_state.requirements_data = req_data
                        
                        # Display requirements summary
                        st.success(f"✅ Found {req_data.get('requirements_count', 0)} requirements")
                        
                        # Show categorized requirements
                        if req_data.get("categorized_requirements"):
                            st.subheader("Requirements by Category")
                            for category, reqs in req_data["categorized_requirements"].items():
                                with st.expander(f"{category} ({len(reqs)} requirements)"):
                                    for req in reqs[:5]:  # Show first 5
                                        st.write(f"• {req['text'][:200]}...")
                        
                        # Show generated instructions
                        if req_data.get("instructions"):
                            with st.expander("📝 Generated Instructions Preview"):
                                st.text(req_data["instructions"][:1000] + "...")
                                
                    except Exception as e:
                        st.error(f"Analysis failed: {str(e)}")
        else:
            st.info("Please upload a fallback document to analyze requirements")

# Tab 3: Workflow Progress (only for complete mode)
if st.session_state.workflow_mode == "complete":
    with tab3:
        st.header("🔄 Workflow Progress")
        
        if st.session_state.workflow_result and st.session_state.workflow_result.get("workflow_id"):
            result = st.session_state.workflow_result
            
            # Workflow ID and duration
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Workflow ID", result["workflow_id"])
            with col2:
                duration = result.get("processing_duration_seconds", 0)
                st.metric("Total Duration", f"{duration:.1f}s")
            
            # Stage progress visualization
            stages_completed = result.get("stages_completed", 0)
            stages_total = result.get("stages_total", 8)
            
            # Progress bar
            progress = stages_completed / stages_total if stages_total > 0 else 0
            st.progress(progress)
            st.caption(f"{stages_completed} of {stages_total} stages completed")
            
            # Workflow stages diagram
            st.subheader("Workflow Stages")
            
            # Create a simple workflow diagram using Plotly
            stages = [
                "Initialization",
                "Document Analysis", 
                "Fallback Processing",
                "Instruction Merging",
                "LLM Processing",
                "Document Modification",
                "Validation",
                "Finalization"
            ]
            
            # Mock stage statuses based on completion
            stage_colors = []
            for i in range(len(stages)):
                if i < stages_completed:
                    stage_colors.append("green")
                elif i == stages_completed:
                    stage_colors.append("orange")
                else:
                    stage_colors.append("lightgray")
            
            fig = go.Figure()
            
            # Add workflow stages as a horizontal bar chart
            fig.add_trace(go.Bar(
                x=[1] * len(stages),
                y=stages,
                orientation='h',
                marker=dict(color=stage_colors),
                text=stages,
                textposition='inside',
                hovertemplate='%{y}<extra></extra>'
            ))
            
            fig.update_layout(
                title="Workflow Pipeline Status",
                xaxis=dict(showticklabels=False, showgrid=False),
                yaxis=dict(showgrid=False),
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Validation results if available
            if result.get("validation_results"):
                st.subheader("✅ Validation Results")
                val_results = result["validation_results"]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("File Size Change", f"{val_results.get('file_size_change_percent', 0):.1f}%")
                with col2:
                    st.metric("Edit Application Rate", f"{val_results.get('edit_application_rate', 0):.1%}")
                with col3:
                    coherence_status = val_results.get('legal_coherence_status', 'unknown')
                    status_color = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(coherence_status, "⚪")
                    st.metric("Coherence Status", f"{status_color} {coherence_status.title()}")
        else:
            st.info("Run the complete workflow to see progress visualization")

# Tab 4: Results & Metrics (for enhanced/complete modes)
if st.session_state.workflow_mode != "simple":
    with tab4:
        st.header("📊 Processing Metrics")
        
        if st.session_state.workflow_result:
            result = st.session_state.workflow_result
            
            # Create metrics dashboard
            col1, col2 = st.columns(2)
            
            with col1:
                # Requirements metrics
                st.subheader("📋 Requirements Processing")
                metrics_data = {
                    "Requirements Extracted": result.get("requirements_extracted", 0),
                    "Requirements Merged": result.get("requirements_merged", 0),
                    "Edits Suggested": result.get("edits_suggested", 0),
                    "Edits Applied": result.get("edits_applied", 0)
                }
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=list(metrics_data.values()),
                    y=list(metrics_data.keys()),
                    orientation='h',
                    marker_color=['lightblue', 'blue', 'lightgreen', 'green']
                ))
                fig.update_layout(
                    title="Processing Pipeline Metrics",
                    xaxis_title="Count",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Coherence score gauge
                st.subheader("⚖️ Legal Coherence Score")
                if result.get("legal_coherence_score") is not None:
                    score = result["legal_coherence_score"]
                    
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number+delta",
                        value=score,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "Coherence Score"},
                        gauge={
                            'axis': {'range': [None, 1]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 0.6], 'color': "lightgray"},
                                {'range': [0.6, 0.8], 'color': "yellow"},
                                {'range': [0.8, 1], 'color': "lightgreen"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 0.7
                            }
                        }
                    ))
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Interpretation
                    if score >= 0.8:
                        st.success("High confidence merge - ready for use")
                    elif score >= 0.6:
                        st.warning("Medium confidence - review recommended")
                    else:
                        st.error("Low confidence - manual review required")
            
            # Processing method info
            st.info(f"Processing Method: {result.get('processing_method', 'Unknown')}")
        else:
            st.info("Process a document to see detailed metrics")

# Tab 5: Help & Guide (for enhanced/complete modes)
if st.session_state.workflow_mode != "simple":
    with tab5:
        st.header("📚 User Guide")
        
        st.markdown("""
        ### Workflow Modes
        
        #### 🔹 Simple (Original)
        - Basic document processing with user instructions only
        - Suitable for straightforward edits
        - Fast processing
        
        #### 🔹 Enhanced (With Fallback)
        - Combines fallback requirements with user instructions
        - Three merge strategies available:
          - **Append**: Fallback requirements first, then user instructions
          - **Prepend**: User instructions first, then fallback requirements
          - **Priority**: Fallback requirements take precedence
        
        #### 🔹 Complete Legal Workflow (Phase 4.1)
        - Full 8-stage processing pipeline
        - Advanced instruction merging (Phase 2.2)
        - Legal coherence validation
        - Comprehensive audit logging
        - Best for critical legal documents
        
        ### Best Practices
        
        1. **Fallback Documents**: Use template documents with standard legal requirements
        2. **User Instructions**: Be specific about changes needed
        3. **Validation**: Review the legal coherence score before using processed documents
        4. **Audit Trail**: Enable audit logging for compliance requirements
        
        ### Understanding Metrics
        
        - **Requirements Extracted**: Number of requirements found in fallback document
        - **Requirements Merged**: Successfully combined requirements after conflict resolution
        - **Legal Coherence Score**: 0-1 score indicating consistency of merged requirements
        - **Edit Application Rate**: Percentage of suggested edits successfully applied
        """)
        
        with st.expander("🔧 Troubleshooting"):
            st.markdown("""
            **Common Issues:**
            
            1. **Low coherence score**: User instructions may conflict with fallback requirements
            2. **Failed edits**: Document structure may not match expected format
            3. **Timeout errors**: Large documents may need more processing time
            
            **Solutions:**
            - Review and clarify user instructions
            - Ensure fallback document is properly formatted
            - Use performance mode settings for large documents
            """)

# Footer
st.markdown("---")
st.caption(f"Legal Document Processor v4.1 - Connected to: {BACKEND_URL}")