"""
Secure file upload validation module for Word Document Chatbot.

This module implements comprehensive security checks for DOCX file uploads:
- Filename and extension validation
- File size limits (prevents DoS attacks)
- MIME type validation using magic numbers (not just extension)
- ZIP structure integrity validation
- ZIP bomb protection (compression ratio and uncompressed size checks)
- Macro detection (rejects macro-enabled documents)
- Path traversal protection

SECURITY NOTE: This module is critical for preventing file-based attacks.
All upload endpoints MUST use validate_docx_upload() before processing.
"""
import io
import magic
import zipfile
from typing import Tuple, Optional
from fastapi import UploadFile

# Configuration - adjust these values based on your requirements
MAX_FILE_SIZE_MB = 10
MAX_UNCOMPRESSED_SIZE_MB = 100
MAX_COMPRESSION_RATIO = 100
ALLOWED_MIME_TYPES = [
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/zip'  # DOCX files are ZIP archives
]


async def validate_docx_upload(file: UploadFile) -> Tuple[bool, Optional[str]]:
    """
    Comprehensive DOCX file validation with security checks.

    Validates:
    - Filename and extension
    - File size limits (prevents DoS)
    - MIME type using magic numbers (prevents extension spoofing)
    - ZIP structure integrity
    - ZIP bomb protection (compression ratio and uncompressed size)
    - Macro detection (rejects VBA macros for security)
    - Path traversal in filename

    Args:
        file: FastAPI UploadFile object

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
        - (True, None) if file passes all validation
        - (False, "error message") if file fails any check
    """

    # 1. Validate filename
    if not file.filename or not file.filename.lower().endswith(".docx"):
        return False, "Only .docx files are supported."

    # Prevent double extension attacks (e.g., "malicious.docx.exe")
    if file.filename.count('.') > 1:
        return False, "Invalid filename format. Multiple extensions not allowed."

    # Prevent path traversal in filename
    if '/' in file.filename or '\\' in file.filename or '..' in file.filename:
        return False, "Invalid characters in filename."

    # Prevent excessively long filenames
    if len(file.filename) > 255:
        return False, "Filename too long (max 255 characters)."

    # 2. Read and validate file size
    file_content = await file.read()
    file_size_mb = len(file_content) / (1024 * 1024)

    if file_size_mb > MAX_FILE_SIZE_MB:
        await file.seek(0)  # Reset for cleanup
        return False, f"File size exceeds maximum allowed size of {MAX_FILE_SIZE_MB}MB."

    if len(file_content) < 100:  # Suspiciously small for a valid DOCX
        await file.seek(0)
        return False, "File is too small to be a valid DOCX document."

    # 3. Validate MIME type using magic numbers (not just file extension)
    try:
        mime_type = magic.from_buffer(file_content, mime=True)
        if mime_type not in ALLOWED_MIME_TYPES:
            await file.seek(0)
            return False, f"Invalid file type. Expected DOCX, got {mime_type}."
    except Exception as e:
        await file.seek(0)
        return False, f"Error detecting file type: {str(e)}"

    # 4. Validate ZIP structure (DOCX is a ZIP archive)
    try:
        with zipfile.ZipFile(io.BytesIO(file_content)) as docx_zip:
            # Check for required DOCX components
            required_files = ['[Content_Types].xml', 'word/document.xml']
            for required_file in required_files:
                if required_file not in docx_zip.namelist():
                    await file.seek(0)
                    return False, f"Invalid DOCX structure: missing {required_file}."

            # 5. ZIP Bomb Protection - check total uncompressed size
            total_uncompressed_size = sum(info.file_size for info in docx_zip.infolist())
            max_uncompressed_bytes = MAX_UNCOMPRESSED_SIZE_MB * 1024 * 1024

            if total_uncompressed_size > max_uncompressed_bytes:
                await file.seek(0)
                return False, "File exceeds maximum uncompressed size limit (potential ZIP bomb)."

            # 6. ZIP Bomb Protection - check compression ratio
            compressed_size = len(file_content)
            if compressed_size > 0:
                compression_ratio = total_uncompressed_size / compressed_size
                if compression_ratio > MAX_COMPRESSION_RATIO:
                    await file.seek(0)
                    return False, f"Suspicious compression ratio detected (potential ZIP bomb). Ratio: {compression_ratio:.2f}:1"

            # 7. Macro Detection - reject macro-enabled documents
            for name in docx_zip.namelist():
                if 'vbaProject.bin' in name or 'macros' in name.lower():
                    await file.seek(0)
                    return False, "Macro-enabled documents are not supported for security reasons."

            # 8. Check for suspicious file names in archive (path traversal in ZIP)
            for name in docx_zip.namelist():
                if '..' in name or name.startswith('/') or '\\' in name:
                    await file.seek(0)
                    return False, "Suspicious file paths detected in DOCX archive."

    except zipfile.BadZipFile:
        await file.seek(0)
        return False, "File is not a valid ZIP/DOCX archive."
    except Exception as e:
        await file.seek(0)
        return False, f"Error validating file structure: {str(e)}"

    # All checks passed - reset file pointer for actual processing
    await file.seek(0)

    return True, None


def get_validation_config() -> dict:
    """
    Get current validation configuration.

    Returns:
        Dictionary containing current validation limits
    """
    return {
        "max_file_size_mb": MAX_FILE_SIZE_MB,
        "max_uncompressed_size_mb": MAX_UNCOMPRESSED_SIZE_MB,
        "max_compression_ratio": MAX_COMPRESSION_RATIO,
        "allowed_mime_types": ALLOWED_MIME_TYPES
    }
