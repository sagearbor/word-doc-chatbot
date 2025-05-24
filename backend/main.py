import os
import shutil
import tempfile
import uuid
from typing import List, Dict, Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from docx import Document

from .llm_handler import get_llm_suggestions, get_llm_analysis
from .word_processor import process_document_with_edits # Ensure this import is correct


app = FastAPI(title="Word Document Processing API")
TEMP_DIR = tempfile.mkdtemp(prefix="wordapp_")


def extract_text(path: str) -> str:
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)


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
async def process_document(
    file: UploadFile = File(...),
    instructions: str = Form(...),
    author_name: Optional[str] = Form(None),
    case_sensitive: bool = Form(True),
    add_comments: bool = Form(True),
):
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are supported.")

    request_id = uuid.uuid4().hex
    input_path = os.path.join(TEMP_DIR, f"{request_id}_input.docx")
    output_path = os.path.join(TEMP_DIR, f"{request_id}_output.docx")

    with open(input_path, "wb") as buff:
        shutil.copyfileobj(file.file, buff)

    doc_text = extract_text(input_path)
    edits = get_llm_suggestions(doc_text, instructions, file.filename)
    if edits is None:
        raise HTTPException(status_code=500, detail="LLM failed to generate suggestions")

    if edits:
        success, log_file, log_details = process_document_with_edits(
            input_docx_path=input_path,
            output_docx_path=output_path,
            edits_to_make=edits,
            author_name=author_name or "AI Reviewer",
            debug_mode_flag=True,
            case_sensitive_flag=case_sensitive,
            add_comments_flag=add_comments,
        )
        if not success:
            raise HTTPException(status_code=500, detail="Word processing failed")
    else:
        shutil.copy(input_path, output_path)
        log_file = None
        log_details = [{"issue": "LLM suggested no changes."}]

    log_content = None
    if log_file and os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            log_content = f.read()
    elif log_details:
        log_content = "\n".join(d.get("issue", "") for d in log_details)

    return JSONResponse(
        {
            "processed_filename": os.path.basename(output_path),
            "download_url": f"/download/{os.path.basename(output_path)}",
            "log_content": log_content,
        }
    )


@app.get("/download/{filename}")
async def download(filename: str):
    file_path = os.path.join(TEMP_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename)


@app.get("/")
async def root():
    return {"message": "API is running"}

