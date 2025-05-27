import os
os.environ['LITELLM_LOG'] = 'DEBUG' # Recommended way to enable LiteLLM debug logs
import shutil
import tempfile
import uuid
from typing import List, Dict, Optional
import traceback 
import json # Make sure json is imported

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from docx import Document

from .llm_handler import get_llm_suggestions, get_llm_analysis
# Import _build_visible_text_map from word_processor
from .word_processor import process_document_with_edits, DEFAULT_AUTHOR_NAME, _build_visible_text_map

app = FastAPI(title="Word Document Processing API")
TEMP_DIR_ROOT = tempfile.mkdtemp(prefix="wordapp_root_")

# MODIFIED extract_text function
def extract_text_for_llm(path: str) -> str:
    """
    Extracts text from the document using _build_visible_text_map 
    to get the 'accepted changes' view for the LLM.
    """
    try:
        doc = Document(path)
        all_paragraphs_text = []
        for p_obj in doc.paragraphs:
            map_text, _ = _build_visible_text_map(p_obj) # Use your function
            all_paragraphs_text.append(map_text)
        return "\n".join(all_paragraphs_text)
    except Exception as e:
        print(f"Error in extract_text_for_llm: {e}")
        traceback.print_exc()
        # Fallback or raise an error if critical
        # For now, try to use python-docx's default as a less ideal fallback.
        # Or, it might be better to let this error propagate if _build_visible_text_map is essential.
        try:
            doc = Document(path)
            return "\n".join(p.text for p in doc.paragraphs if p.text)
        except Exception as e_fallback:
            print(f"Fallback text extraction also failed: {e_fallback}")
            return ""


@app.post("/analyze-document/")
async def analyze_document_endpoint(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Invalid file type or missing filename. Only .docx files are accepted.")

    request_id = str(uuid.uuid4())
    original_filename = os.path.basename(file.filename) 
    input_docx_path = os.path.join(TEMP_DIR_ROOT, f"{request_id}_analysis_{original_filename}")

    try:
        with open(input_docx_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Use the new extraction method for analysis text
        document_text = extract_text_for_llm(input_docx_path) 

        # Add a debug print for the text being sent for analysis
        print("\n[MAIN_PY_DEBUG] Text sent for /analyze-document/ LLM:")
        print(document_text[:1000] + "..." if len(document_text) > 1000 else document_text) # Print snippet
        print("[MAIN_PY_DEBUG] End of text for /analyze-document/ LLM.\n")

        analysis = get_llm_analysis(document_text, original_filename)

        if analysis is None: 
            raise HTTPException(status_code=500, detail="Failed to get analysis from LLM.")

        return JSONResponse(content={"analysis": analysis})
    except HTTPException: 
        raise
    except Exception as e: 
        print(f"Error during document analysis: {e}") 
        traceback.print_exc() 
        raise HTTPException(status_code=500, detail=f"An error occurred during document analysis: {str(e)}")
    finally:
        if os.path.exists(input_docx_path):
            try: os.remove(input_docx_path)
            except Exception as e_clean: print(f"Error cleaning up analysis file {input_docx_path}: {e_clean}")


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
    if not file.filename or not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are supported.")

    request_id = uuid.uuid4().hex
    base_input_filename = os.path.basename(file.filename) 
    input_path = os.path.join(TEMP_DIR_ROOT, f"{request_id}_input_{base_input_filename}")
    output_path = os.path.join(TEMP_DIR_ROOT, f"{request_id}_output_{base_input_filename}")

    try:
        with open(input_path, "wb") as buff:
            shutil.copyfileobj(file.file, buff)

        # Use the new extraction method for suggestions text
        doc_text_for_llm = extract_text_for_llm(input_path) 

        # Add a debug print for the text being sent for suggestions
        print("\n[MAIN_PY_DEBUG] Text sent for /process-document/ LLM (get_llm_suggestions):")
        print(doc_text_for_llm[:1000] + "..." if len(doc_text_for_llm) > 1000 else doc_text_for_llm) # Print snippet
        print("[MAIN_PY_DEBUG] End of text for /process-document/ LLM.\n")

        edits: Optional[List[Dict]] = get_llm_suggestions(doc_text_for_llm, instructions, base_input_filename)

        print("\n[MAIN_PY_DEBUG] Raw edits from LLM (get_llm_suggestions output):") 
        if edits is not None:                                                      
            print(json.dumps(edits, indent=2))                                     
        else:                                                                      
            print("LLM returned None for edits.")                                  
        print("[MAIN_PY_DEBUG] End of raw edits from LLM.\n")

        if edits is None: 
            raise HTTPException(status_code=500, detail="LLM failed to generate or return valid suggestions format (returned None).")

        processed_edits_count = 0
        log_file_path_returned: Optional[str] = None
        log_details_returned: List[Dict] = [] 

        if edits: 
            wp_success, log_file_path_returned, log_details_returned, processed_edits_count = process_document_with_edits(
                input_docx_path=input_path, # word_processor still works on the original file path
                output_docx_path=output_path,
                edits_to_make=edits,
                author_name=author_name if author_name else DEFAULT_AUTHOR_NAME,
                debug_mode_flag=debug_mode,              
                extended_debug_mode_flag=extended_debug_mode, 
                case_sensitive_flag=case_sensitive,
                add_comments_param=add_comments,         
            )
            # ... (rest of the endpoint is largely the same as the last version you provided for main.py)
            if not wp_success: 
                error_issue = "Word processing script encountered a critical failure."
                if log_details_returned and isinstance(log_details_returned, list) and log_details_returned[0].get("issue"):
                    error_issue = str(log_details_returned[0]["issue"])
                raise HTTPException(status_code=500, detail=error_issue)
        else: 
            shutil.copy(input_path, output_path) 
            log_details_returned = [{"issue": "LLM suggested no changes for the given instructions.", "type": "Info"}]
            processed_edits_count = 0 

        log_content_for_response: Optional[str] = None
        if log_file_path_returned and os.path.exists(log_file_path_returned):
            with open(log_file_path_returned, "r", encoding="utf-8") as f_log:
                log_content_for_response = f_log.read()
        elif log_details_returned: 
            log_content_for_response = "\n".join(
                f"Type: {d.get('type', 'Log')}, Issue: {d.get('issue', 'N/A')}, Para: {d.get('paragraph_index', -1)+1 if isinstance(d.get('paragraph_index'), int) else 'N/A'}, Old: '{d.get('specific_old_text', '')}'" 
                for d in log_details_returned
            )

        total_suggested_edits = len(edits) 
        final_status_message = "Processing complete."

        if total_suggested_edits == 0:
            final_status_message = "Processing complete. The LLM suggested no changes."
        elif processed_edits_count == 0 and total_suggested_edits > 0:
            final_status_message = f"Processing complete. {total_suggested_edits} edit(s) were suggested by the LLM, but none were applied by the processor. Please check the log for details (e.g., context not found, boundary rule skips, ambiguities)."
        elif processed_edits_count < total_suggested_edits:
            final_status_message = f"Processing complete. {processed_edits_count} out of {total_suggested_edits} suggested changes were applied. Some edits may have been skipped or were ambiguous. Please check the log for details."
        elif processed_edits_count == total_suggested_edits: 
             final_status_message = f"Processing complete. All {processed_edits_count} suggested changes were successfully applied."

        if not os.path.exists(output_path) and os.path.exists(input_path):
             shutil.copy(input_path, output_path) 

        return JSONResponse(
            content={
                "processed_filename": os.path.basename(output_path),
                "download_url": f"/download/{os.path.basename(output_path)}", 
                "log_content": log_content_for_response,
                "status_message": final_status_message,
                "issues_count": len(log_details_returned) if log_details_returned else 0, 
                "edits_applied_count": processed_edits_count,
                "edits_suggested_count": total_suggested_edits
            }
        )

    except HTTPException: 
        raise
    except Exception as e: 
        print(f"Error in /process-document/ endpoint: {e}")
        traceback.print_exc() 
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred on the server: {str(e)}")
    finally:
        if os.path.exists(input_path):
            try: os.remove(input_path)
            except Exception as e_clean_in: print(f"Error cleaning up input file {input_path}: {e_clean_in}")

# ... (rest of main.py - download, shutdown, root - assumed unchanged)
@app.get("/download/{filename}")
async def download_file_presumably_from_temp_dir(filename: str):
    if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
        raise HTTPException(status_code=400, detail="Invalid filename.")

    file_path = os.path.join(TEMP_DIR_ROOT, filename)
    if not os.path.isfile(file_path): 
        print(f"Download request for non-existent or non-file path: {file_path}")
        raise HTTPException(status_code=404, detail="File not found or is not accessible.")

    return FileResponse(
        file_path, 
        filename=filename, 
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )

@app.on_event("shutdown")
def cleanup_temp_dir(): 
    print(f"Attempting to clean up temporary directory: {TEMP_DIR_ROOT}")
    try:
        if os.path.exists(TEMP_DIR_ROOT):
            shutil.rmtree(TEMP_DIR_ROOT)
            print(f"Successfully removed temporary directory: {TEMP_DIR_ROOT}")
    except Exception as e:
        print(f"Error during temporary directory cleanup: {e}")
        traceback.print_exc()

@app.get("/")
async def root():
    return {"message": "Word Document Processing API is running."}