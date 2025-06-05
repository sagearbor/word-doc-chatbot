import os
os.environ['LITELLM_LOG'] = 'DEBUG' 
import shutil
import tempfile
import uuid
from typing import List, Dict, Optional
import traceback 
import json

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
# docx.Document is used by extract_text_for_llm if that's kept, and by word_processor
from docx import Document 

# Corrected imports based on new llm_handler and word_processor structure
from .llm_handler import (
    get_llm_suggestions,
    get_llm_analysis_from_summary,   # For Approach 1
    get_llm_analysis_from_raw_xml    # For Approach 2
)
from .word_processor import (
    process_document_with_edits,
    DEFAULT_AUTHOR_NAME,
    _build_visible_text_map,         # Used by extract_text_for_llm
    extract_tracked_changes_as_text, # For Approach 1
    get_document_xml_raw_text        # For Approach 2
)

app = FastAPI(title="Word Document Processing API")

# Ensure TEMP_DIR_ROOT is defined at the module level
TEMP_DIR_ROOT = tempfile.mkdtemp(prefix="wordapp_root_")
print(f"Temporary root directory created at: {TEMP_DIR_ROOT}")


# This function is used by /process-document/ for LLM suggestions, keep it.
def extract_text_for_llm(path: str) -> str:
    try:
        doc = Document(path) # Requires python-docx Document
        all_paragraphs_text = []
        for p_obj in doc.paragraphs:
            map_text, _ = _build_visible_text_map(p_obj)
            all_paragraphs_text.append(map_text)
        return "\n".join(all_paragraphs_text)
    except Exception as e:
        print(f"Error in extract_text_for_llm: {e}")
        traceback.print_exc()
        try: # Fallback
            doc = Document(path)
            return "\n".join(p.text for p in doc.paragraphs if p.text)
        except Exception as e_fallback:
            print(f"Fallback text extraction also failed: {e_fallback}")
            return ""


@app.post("/analyze-document/")
async def analyze_document_endpoint(
    file: UploadFile = File(...),
    analysis_mode: str = Form("summary") # Default to "summary", options: "summary", "raw_xml"
):
    if not file.filename or not file.filename.lower().endswith(".docx"): # Check lower() for .DOCX
        raise HTTPException(status_code=400, detail="Invalid file type or missing filename. Only .docx files are accepted.")

    request_id = str(uuid.uuid4())
    original_filename = os.path.basename(file.filename) 
    input_docx_path = os.path.join(TEMP_DIR_ROOT, f"{request_id}_analysis_{original_filename}")

    print(f"[PID:{os.getpid()}] /analyze-document/ received for '{original_filename}', mode: '{analysis_mode}'")

    try:
        os.makedirs(TEMP_DIR_ROOT, exist_ok=True) # Ensure temp dir exists
        with open(input_docx_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"[PID:{os.getpid()}] File '{original_filename}' saved to '{input_docx_path}'")

        analysis_result_text: Optional[str] = None

        if analysis_mode == "summary":
            print(f"[PID:{os.getpid()}] Using 'summary' analysis mode for {original_filename}.")
            summary_of_changes = extract_tracked_changes_as_text(input_docx_path)
            
            print(f"[PID:{os.getpid()}] Summary of changes extracted (first 500 chars):\n{summary_of_changes[:500]}...")
            
            # The get_llm_analysis_from_summary function now handles "No changes" or "Error_Internal" itself
            analysis_result_text = get_llm_analysis_from_summary(summary_of_changes, original_filename)

        elif analysis_mode == "raw_xml":
            print(f"[PID:{os.getpid()}] Using 'raw_xml' analysis mode for {original_filename}.")
            raw_xml_content = get_document_xml_raw_text(input_docx_path)

            print(f"[PID:{os.getpid()}] Raw XML content extracted (first 500 chars):\n{raw_xml_content[:500]}...")

            if raw_xml_content.startswith("Error_Internal:"):
                 analysis_result_text = raw_xml_content # Pass through extraction error
            else:
                # Basic check for very large XML that might be problematic
                # This is a character count, not token count. Actual token count depends on model.
                MAX_RAW_XML_CHARS_FOR_LLM = 150 * 1024 # Approx 150KB as a very rough limit for the input string
                if len(raw_xml_content) > MAX_RAW_XML_CHARS_FOR_LLM:
                    warning_msg = (
                        f"Warning: The document's internal XML content is very large "
                        f"({len(raw_xml_content) // 1024}KB). Analysis might be slow, incomplete, or fail. "
                        "Consider using the 'Summarize Extracted Changes (Concise)' mode for very large/complex documents."
                    )
                    print(f"[PID:{os.getpid()}] {warning_msg}")
                    # We can still proceed but the LLM might struggle.
                    # Or, return this warning to the user:
                    # analysis_result_text = warning_msg 
                
                if analysis_result_text is None: # If not set by size warning
                    analysis_result_text = get_llm_analysis_from_raw_xml(raw_xml_content, original_filename)
        else:
            # This error indicates a problem with how analysis_mode is sent or handled, not user input usually.
            err_msg = f"Error_Server: Invalid analysis_mode '{analysis_mode}' specified. Must be 'summary' or 'raw_xml'."
            print(f"[PID:{os.getpid()}] {err_msg}")
            # Return as 200 so Streamlit can display the error message from the "analysis" field
            return JSONResponse(content={"analysis": err_msg}, status_code=200)

        # Handle cases where LLM calls might return None or a specific error string
        if analysis_result_text is None:
            analysis_result_text = "Error_Server: Analysis result was unexpectedly empty after LLM call."
            print(f"[PID:{os.getpid()}] [WARN] {analysis_result_text} for {original_filename}, mode {analysis_mode}")
        
        print(f"[PID:{os.getpid()}] Analysis result for LLM (first 300 chars): {analysis_result_text[:300]}...")
        return JSONResponse(content={"analysis": analysis_result_text})

    except HTTPException:
        raise # Re-raise HTTPExceptions to let FastAPI handle them as actual HTTP errors
    except Exception as e: 
        print(f"[PID:{os.getpid()}] Critical error in /analyze-document/ for '{original_filename}' (mode: {analysis_mode}): {e}")
        traceback.print_exc() 
        # Return a 200 with a server error message for Streamlit to display from the "analysis" field
        return JSONResponse(content={"analysis": f"Error_Server: An unexpected critical error occurred on the server: {str(e)}"}, status_code=200)
    finally:
        if os.path.exists(input_docx_path):
            try: 
                os.remove(input_docx_path)
                print(f"[PID:{os.getpid()}] Cleaned up temp file: {input_docx_path}")
            except Exception as e_clean: 
                print(f"[PID:{os.getpid()}] Error cleaning up analysis file {input_docx_path}: {e_clean}")


@app.post("/process-document/")
async def process_document(
    file: UploadFile = File(...),
    instructions: str = Form(...),
    author_name: Optional[str] = Form(None),
    case_sensitive: bool = Form(True),
    add_comments: bool = Form(True),
    debug_mode: bool = Form(False),          
    extended_debug_mode: bool = Form(False)  
):
    # ... (keep existing /process-document/ endpoint logic) ...
    if not file.filename or not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are supported.")
    request_id = uuid.uuid4().hex
    base_input_filename = os.path.basename(file.filename) 
    input_path = os.path.join(TEMP_DIR_ROOT, f"{request_id}_input_{base_input_filename}")
    output_path = os.path.join(TEMP_DIR_ROOT, f"{request_id}_output_{base_input_filename}")
    try:
        os.makedirs(TEMP_DIR_ROOT, exist_ok=True)
        with open(input_path, "wb") as buff: shutil.copyfileobj(file.file, buff)
        doc_text_for_llm = extract_text_for_llm(input_path) 
        print("\n[MAIN_PY_DEBUG] Text sent for /process-document/ LLM (get_llm_suggestions):")
        print(doc_text_for_llm[:1000] + "..." if len(doc_text_for_llm) > 1000 else doc_text_for_llm)
        print("[MAIN_PY_DEBUG] End of text for /process-document/ LLM.\n")
        edits: Optional[List[Dict]] = get_llm_suggestions(doc_text_for_llm, instructions, base_input_filename)
        print("\n[MAIN_PY_DEBUG] Raw edits from LLM (get_llm_suggestions output):") 
        if edits is not None: print(json.dumps(edits, indent=2))                                     
        else: print("LLM returned None for edits.")                                  
        print("[MAIN_PY_DEBUG] End of raw edits from LLM.\n")
        if edits is None: 
            raise HTTPException(status_code=500, detail="LLM failed to generate or return valid suggestions format (returned None).")
        processed_edits_count = 0
        log_file_path_returned: Optional[str] = None
        log_details_returned: List[Dict] = [] 
        if edits: 
            wp_success, log_file_path_returned, log_details_returned, processed_edits_count = process_document_with_edits(
                input_docx_path=input_path, output_docx_path=output_path, edits_to_make=edits,
                author_name=author_name if author_name else DEFAULT_AUTHOR_NAME,
                debug_mode_flag=debug_mode, extended_debug_mode_flag=extended_debug_mode, 
                case_sensitive_flag=case_sensitive, add_comments_param=add_comments,         
            )
            if not wp_success: 
                error_issue = "Word processing script encountered a critical failure."
                if log_details_returned and isinstance(log_details_returned, list) and log_details_returned[0].get("issue"):
                    error_issue = str(log_details_returned[0]["issue"])
                raise HTTPException(status_code=500, detail=error_issue)
        else:  # if not edits (LLM suggested no changes)
            shutil.copy(input_path, output_path) 
            log_details_returned = [{"issue": "LLM suggested no changes for the given instructions.", "type": "Info"}]
            processed_edits_count = 0 

        log_content_for_response: str # Make it a string type from the start

        if log_file_path_returned and os.path.exists(log_file_path_returned):
            with open(log_file_path_returned, "r", encoding="utf-8") as f_log:
                log_content_for_response = f_log.read()
        elif log_details_returned: # This is the List[Dict] from ambiguous_or_failed_changes_log
            log_content_for_response = "\n".join( # This will be an empty string if log_details_returned is empty
                f"Type: {d.get('type', 'Log')}, Issue: {d.get('issue', 'N/A')}, "
                f"Para: {d.get('paragraph_index', -1)+1 if isinstance(d.get('paragraph_index'), int) else 'N/A'}, "
                f"Old: '{d.get('specific_old_text', '')}'"
                for d in log_details_returned
            )
        else: # log_details_returned is None (shouldn't happen if initialized to []) OR was an empty list and caught by prior elif being false.
              # This 'else' means no log file AND log_details_returned was effectively empty or None.
            if edits: # If LLM suggested edits but they resulted in an empty log from word_processor
                log_content_for_response = "No specific processing issues, warnings, or errors were recorded in the detailed log for the suggested edits. They may have been skipped (e.g., 'context not found') without being logged as specific issues here."
            else: # LLM suggested no edits in the first place (this path is handled by the outer 'if edits:' else block mostly)
                 log_content_for_response = "The AI suggested no changes, so no processing log was generated for new edits."
        
        # If log_content_for_response became "" from an empty log_details_returned list, provide a default message.
        if not log_content_for_response and isinstance(log_details_returned, list) and not log_details_returned:
            log_content_for_response = "No specific processing issues, warnings, or errors were recorded in the detailed log for the suggested edits."
        
        # --- THIS LOGIC MUST BE OUTSIDE THE PREVIOUS IF ---
        total_suggested_edits = len(edits) 
        final_status_message = "Processing complete." # Default status

        if total_suggested_edits == 0:
            final_status_message = "Processing complete. The LLM suggested no changes."
        elif processed_edits_count == 0 and total_suggested_edits > 0:
            final_status_message = f"Processing complete. {total_suggested_edits} edit(s) were suggested by the LLM, but none were applied by the processor. Please check the log for details (e.g., context not found, boundary rule skips, ambiguities)."
        elif processed_edits_count < total_suggested_edits:
            final_status_message = f"Processing complete. {processed_edits_count} out of {total_suggested_edits} suggested changes were applied. Some edits may have been skipped or were ambiguous. Please check the log for details."
        elif processed_edits_count == total_suggested_edits and total_suggested_edits > 0: # Ensure we don't say "all 0"
             final_status_message = f"Processing complete. All {processed_edits_count} suggested changes were successfully applied."

        if not os.path.exists(output_path) and os.path.exists(input_path): # Ensure output file exists
             shutil.copy(input_path, output_path) 

        return JSONResponse(
            content={
                "processed_filename": os.path.basename(output_path),
                "download_url": f"/download/{os.path.basename(output_path)}", 
                "log_content": log_content_for_response, # This should now always be a non-None string
                "status_message": final_status_message,
                "issues_count": len(log_details_returned) if log_details_returned else 0, 
                "edits_applied_count": processed_edits_count,
                "edits_suggested_count": total_suggested_edits
            }
        )

    except HTTPException: raise
    except Exception as e: 
        print(f"Error in /process-document/ endpoint: {e}"); traceback.print_exc() 
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred on the server: {str(e)}")
    finally:
        if os.path.exists(input_path):
            try: os.remove(input_path)
            except Exception as e_clean_in: print(f"Error cleaning up input file {input_path}: {e_clean_in}")


@app.get("/download/{filename}")
async def download_file_presumably_from_temp_dir(filename: str):
    # ... (keep existing /download/ endpoint logic) ...
    if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
        raise HTTPException(status_code=400, detail="Invalid filename.")
    file_path = os.path.join(TEMP_DIR_ROOT, filename)
    if not os.path.isfile(file_path): 
        print(f"Download request for non-existent or non-file path: {file_path}")
        raise HTTPException(status_code=404, detail="File not found or is not accessible.")
    return FileResponse(file_path, filename=filename, media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

@app.on_event("shutdown")
def cleanup_temp_dir(): 
    # ... (keep existing shutdown event logic) ...
    print(f"Attempting to clean up temporary directory: {TEMP_DIR_ROOT}")
    try:
        if os.path.exists(TEMP_DIR_ROOT):
            shutil.rmtree(TEMP_DIR_ROOT)
            print(f"Successfully removed temporary directory: {TEMP_DIR_ROOT}")
    except Exception as e:
        print(f"Error during temporary directory cleanup: {e}"); traceback.print_exc()

@app.get("/")
async def root():
    # ... (keep existing root endpoint logic) ...
    return {"message": "Word Document Processing API is running."}