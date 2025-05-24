import os
import shutil
import tempfile
import uuid
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional, List, Dict
import python_docx_oss_block_patches # Important for python-docx on some systems
#  Note on backend/main.py:
#     The line import python_docx_oss_block_patches is added. Sometimes python-docx has issues on certain OS/Python combinations (especially related to lxml) when running in server environments. This import attempts to apply common patches. You might need to install it: pip install python-docx-oss-block-patches. If you don't face issues, you can remove this line and the dependency.


from docx import Document as DocxReader # To read text from docx

from .llm_handler import get_llm_suggestions, get_llm_analysis
from .word_processor import process_document_with_edits # Ensure this import is correct

app = FastAPI(title="Word Document Processing API")

# Ensure a directory for uploads and outputs exists (temporary for this example)
# In a real app, you might use cloud storage or a more robust temporary file system.
TEMP_DIR = tempfile.mkdtemp(prefix="wordapp_")
print(f"Temporary directory for file operations: {TEMP_DIR}")


def get_document_text(file_path: str) -> str:
    """Extracts all paragraph text from a DOCX file."""
    try:
        doc = DocxReader(file_path)
        full_text = [para.text for para in doc.paragraphs]
        return "\n".join(full_text)
    except Exception as e:
        print(f"Error reading text from docx file {file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Could not read text from DOCX file: {e}")


@app.post("/analyze-document/")
async def analyze_document_endpoint(file: UploadFile = File(...)):
    """Analyze a DOCX file and return LLM recommendations."""
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .docx files are accepted.")

    request_id = str(uuid.uuid4())
    original_filename = file.filename
    input_docx_path = os.path.join(TEMP_DIR, f"{request_id}_analysis_{original_filename}")

    try:
        with open(input_docx_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        document_text = get_document_text(input_docx_path)
        analysis = get_llm_analysis(document_text, original_filename)

        if analysis is None:
            raise HTTPException(status_code=500, detail="Failed to get analysis from LLM.")

        return JSONResponse(content={"analysis": analysis})
    finally:
        if os.path.exists(input_docx_path):
            try:
                os.remove(input_docx_path)
            except Exception as e_clean:
                print(f"Error cleaning up analysis file {input_docx_path}: {e_clean}")


@app.post("/process-document/")
async def process_document_endpoint(
    file: UploadFile = File(...),
    instructions: str = Form(...),
    author_name: Optional[str] = Form(None), # Optional author from UI
    case_sensitive: Optional[bool] = Form(True), # Default to True
    add_comments: Optional[bool] = Form(True)    # Default to True
):
    """
    Endpoint to upload a Word document and processing instructions.
    1. Receives DOCX file and instructions.
    2. Saves the uploaded file temporarily.
    3. Extracts text from the DOCX for the LLM.
    4. Calls LLM to get change suggestions.
    5. Calls word_processor to apply changes.
    6. Returns the processed document and any logs.
    """
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .docx files are accepted.")

    request_id = str(uuid.uuid4())
    original_filename = file.filename
    input_docx_path = os.path.join(TEMP_DIR, f"{request_id}_input_{original_filename}")
    output_docx_path = os.path.join(TEMP_DIR, f"{request_id}_output_{original_filename}")
    
    # Log file path will be determined by word_processor, typically in the same dir as output_docx_path
    error_log_content = None # To store content of the error log if generated

    try:
        # 1. Save uploaded file
        with open(input_docx_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"File '{original_filename}' saved to '{input_docx_path}'")

        # 2. Extract text for LLM
        try:
            document_text_for_llm = get_document_text(input_docx_path)
            if not document_text_for_llm.strip():
                 print(f"Warning: Document '{original_filename}' seems to be empty or contains no extractable text.")
                 # Allow processing to continue, LLM might handle this or word_processor will find no text.
        except HTTPException as e: # Catch error from get_document_text
            raise e # Re-raise it, as it's already an HTTPException
        except Exception as e:
            print(f"Unexpected error extracting text for {original_filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to extract text from document: {e}")


        # 3. Call LLM for suggestions
        print(f"Sending to LLM. Instructions: {instructions[:100]}...")
        llm_edits: Optional[List[Dict]] = get_llm_suggestions(document_text_for_llm, instructions, original_filename)

        if llm_edits is None:
            raise HTTPException(status_code=500, detail="Failed to get suggestions from LLM. Check backend logs.")
        
        if not llm_edits: # Empty list means LLM suggested no changes
            print(f"LLM suggested no changes for '{original_filename}'. Returning original file content or a copy.")
            # If no edits, we can return the original file or a copy named as output
            # For consistency, let's make a copy to the output path and return that
            shutil.copy(input_docx_path, output_docx_path)
            return JSONResponse(content={
                "message": "LLM suggested no changes. Original document returned.",
                "processed_filename": os.path.basename(output_docx_path),
                "download_url": f"/download/{os.path.basename(output_docx_path)}",
                "log_filename": None,
                "log_url": None,
                "log_content": "LLM suggested no changes." # Provide log content directly
            })

        print(f"LLM returned {len(llm_edits)} edit suggestions for '{original_filename}'.")

        # 4. Call word processor
        wp_author_name = author_name if author_name else "LLM Auto-Editor" # Use provided author or default
        
        print(f"Processing Word document with: author='{wp_author_name}', case_sensitive={case_sensitive}, add_comments={add_comments}")

        success, error_log_file_path, processing_log_details = process_document_with_edits(
            input_docx_path=input_docx_path,
            output_docx_path=output_docx_path,
            edits_to_make=llm_edits,
            author_name=wp_author_name,
            debug_mode_flag=True, # Enable word_processor debug for now, can be configured
            case_sensitive_flag=case_sensitive,
            add_comments_flag=add_comments
        )

        if not success:
            # This implies a major failure in process_document_with_edits itself (e.g., can't save output)
            # The processing_log_details will contain information about what went wrong.
            log_summary = "Word processing failed. " + (processing_log_details[0].get("issue") if processing_log_details else "Unknown error.")
            raise HTTPException(status_code=500, detail=log_summary)

        log_filename = None
        log_download_url = None
        if error_log_file_path and os.path.exists(error_log_file_path):
            log_filename = os.path.basename(error_log_file_path)
            log_download_url = f"/download/{log_filename}"
            try:
                with open(error_log_file_path, "r", encoding="utf-8") as lf:
                    error_log_content = lf.read()
            except Exception as e_log:
                print(f"Could not read log file {error_log_file_path}: {e_log}")
                error_log_content = f"Log file was generated ({log_filename}) but could not be read by the server."
        elif processing_log_details: # If no log file, but details exist (e.g. successful processing but with warnings)
            error_log_content = "Processing completed. Review of changes and potential issues:\n"
            for entry in processing_log_details:
                 error_log_content += f"- {entry.get('issue', 'N/A')} (Context: {entry.get('contextual_old_text', 'N/A')[:30]}...)\n"
        else:
            error_log_content = "Processing completed successfully with no specific issues logged by word_processor."


        # 5. Return response with download link for the processed file
        return JSONResponse(content={
            "message": "Document processed successfully.",
            "processed_filename": os.path.basename(output_docx_path),
            "download_url": f"/download/{os.path.basename(output_docx_path)}",
            "log_filename": log_filename,
            "log_url": log_download_url,
            "log_content": error_log_content
        })

    except HTTPException as http_exc: # Re-raise HTTPExceptions
        raise http_exc
    except Exception as e:
        print(f"An unexpected error occurred during processing: {e}")
        # Log the full traceback for debugging on the server
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")
    finally:
        # Clean up the originally uploaded file.
        # Output file and log file are kept for download via /download/ endpoint.
        # A more robust cleanup strategy would be needed for production (e.g., TTL for temp files).
        if os.path.exists(input_docx_path):
            try:
                # os.remove(input_docx_path)
                print(f"Note: Input file '{input_docx_path}' kept for debugging. Remove os.remove comment for cleanup.")
            except Exception as e_clean:
                print(f"Error cleaning up input file {input_docx_path}: {e_clean}")
        # The output_docx_path and error_log_file_path should NOT be cleaned here
        # as they are needed for the /download endpoint. They can be cleaned up later.

@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    Serves a file from the temporary directory.
    In a production app, use a more secure way to handle file serving and cleanup.
    """
    file_path = os.path.join(TEMP_DIR, filename)
    if os.path.exists(file_path):
        # Add headers to suggest download and preserve original filename if it was encoded
        # For simplicity, using the generated filename.
        return FileResponse(path=file_path, filename=filename, media_type='application/octet-stream')
    else:
        raise HTTPException(status_code=404, detail="File not found. It may have been cleaned up or never generated.")

# Basic root endpoint
@app.get("/")
async def root():
    return {"message": "Word Document Processing API is running. Use the /process-document/ endpoint."}

# Cleanup TEMP_DIR on shutdown (optional, and might not run on all server stop signals)
# For robust cleanup, a scheduled task or manual cleanup is better.
# @app.on_event("shutdown")
# def shutdown_event():
#     print(f"Attempting to clean up temporary directory: {TEMP_DIR}")
#     try:
#         shutil.rmtree(TEMP_DIR)
#         print(f"Successfully removed temporary directory: {TEMP_DIR}")
#     except Exception as e:
#         print(f"Error cleaning up temporary directory {TEMP_DIR}: {e}")
