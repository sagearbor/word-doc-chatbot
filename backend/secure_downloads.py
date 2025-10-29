"""
Secure file download system with token-based access.

This module implements a secure download system that prevents path traversal attacks by:
- Using cryptographically secure random tokens instead of filenames in URLs
- Validating canonical paths to ensure files are within allowed directories
- Implementing token expiration
- Detecting and blocking symlink attacks
- Automatic cleanup of expired tokens

SECURITY NOTE: Never expose file paths directly in download URLs.
Always use register_download() to create secure download tokens.
"""
import secrets
import datetime
import os
from pathlib import Path
from typing import Dict, Optional
from fastapi import HTTPException
from fastapi.responses import FileResponse


# Global registry for valid downloads
# In production, consider using Redis or similar for distributed systems
VALID_DOWNLOADS: Dict[str, Dict] = {}


def register_download(
    file_path: str,
    original_filename: str,
    allowed_directory: str,
    expiration_minutes: int = 60
) -> str:
    """
    Register a file for download and return a secure token.

    This function creates a cryptographically secure token that can be used
    to download a file without exposing the file path in the URL.

    Args:
        file_path: Absolute path to the file to be downloaded
        original_filename: Original filename to use for the download
        allowed_directory: Base directory that file must be within
        expiration_minutes: Token expiration time in minutes (default 60)

    Returns:
        Download token (secure random string)

    Raises:
        ValueError: If file path is outside allowed directory
    """
    # Validate that file is within allowed directory (canonical path check)
    allowed_dir_canonical = Path(allowed_directory).resolve()
    file_path_canonical = Path(file_path).resolve()

    if not str(file_path_canonical).startswith(str(allowed_dir_canonical)):
        raise ValueError(f"File path {file_path} is outside allowed directory {allowed_directory}")

    # Generate cryptographically secure token
    download_token = secrets.token_urlsafe(32)

    # Register download with expiration
    VALID_DOWNLOADS[download_token] = {
        "path": str(file_path_canonical),
        "filename": original_filename,
        "allowed_directory": str(allowed_dir_canonical),
        "expires": datetime.datetime.now() + datetime.timedelta(minutes=expiration_minutes),
        "created_at": datetime.datetime.now()
    }

    return download_token


async def serve_download(download_token: str) -> FileResponse:
    """
    Serve a file download using a secure token.

    This function performs multiple security checks:
    - Validates token format
    - Checks token existence and expiration
    - Validates canonical path (prevents path traversal)
    - Detects symlinks (prevents symlink attacks)
    - Ensures file is within allowed directory

    Args:
        download_token: The secure download token

    Returns:
        FileResponse for the requested file

    Raises:
        HTTPException: If token is invalid, expired, or file has security issues
    """
    # Validate token format (tokens from token_urlsafe(32) are 43 chars)
    if len(download_token) != 43:
        raise HTTPException(status_code=400, detail="Invalid download token format.")

    # Check if token exists
    if download_token not in VALID_DOWNLOADS:
        raise HTTPException(status_code=404, detail="File not found or download link expired.")

    download_info = VALID_DOWNLOADS[download_token]

    # Check expiration
    if datetime.datetime.now() > download_info["expires"]:
        del VALID_DOWNLOADS[download_token]
        raise HTTPException(status_code=410, detail="Download link has expired.")

    file_path = download_info["path"]
    original_filename = download_info["filename"]
    allowed_directory = download_info["allowed_directory"]

    # SECURITY: Verify file is within allowed directory (canonical path check)
    allowed_dir_canonical = Path(allowed_directory).resolve()

    try:
        file_path_canonical = Path(file_path).resolve()
    except (OSError, RuntimeError) as e:
        print(f"SECURITY: Invalid file path in download. Token: {download_token}, Error: {e}")
        raise HTTPException(status_code=400, detail="Invalid file path.")

    # Ensure file is within allowed directory
    if not str(file_path_canonical).startswith(str(allowed_dir_canonical)):
        # Log security violation
        print(f"SECURITY: Path traversal attempt blocked. Token: {download_token}, "
              f"Path: {file_path}, Allowed: {allowed_directory}")
        raise HTTPException(status_code=403, detail="Access denied.")

    # SECURITY: Verify file exists and is NOT a symlink
    if not file_path_canonical.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    if file_path_canonical.is_symlink():
        print(f"SECURITY: Symlink download attempt blocked. Token: {download_token}, Path: {file_path}")
        raise HTTPException(status_code=403, detail="Access denied.")

    # Return file
    try:
        response = FileResponse(
            str(file_path_canonical),
            filename=original_filename,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

        # Optional: Invalidate token after download (one-time use)
        # Uncomment the next line to make tokens single-use
        # del VALID_DOWNLOADS[download_token]

        return response
    except Exception as e:
        print(f"Error serving file: {e}")
        raise HTTPException(status_code=500, detail="Error downloading file.")


def cleanup_expired_tokens() -> int:
    """
    Cleanup expired download tokens.

    This should be called periodically (e.g., every 5 minutes) to remove
    expired tokens from memory.

    Returns:
        Number of tokens cleaned up
    """
    now = datetime.datetime.now()
    expired = [token for token, info in VALID_DOWNLOADS.items() if now > info["expires"]]

    for token in expired:
        del VALID_DOWNLOADS[token]

    if expired:
        print(f"Cleaned up {len(expired)} expired download tokens")

    return len(expired)


def get_download_stats() -> dict:
    """
    Get statistics about the download system.

    Returns:
        Dictionary containing download system statistics
    """
    now = datetime.datetime.now()
    active_tokens = sum(1 for info in VALID_DOWNLOADS.values() if now <= info["expires"])
    expired_tokens = len(VALID_DOWNLOADS) - active_tokens

    return {
        "total_tokens": len(VALID_DOWNLOADS),
        "active_tokens": active_tokens,
        "expired_tokens": expired_tokens
    }


def invalidate_token(download_token: str) -> bool:
    """
    Manually invalidate a download token.

    Args:
        download_token: The token to invalidate

    Returns:
        True if token was found and removed, False otherwise
    """
    if download_token in VALID_DOWNLOADS:
        del VALID_DOWNLOADS[download_token]
        return True
    return False


def clear_all_tokens():
    """
    Clear all download tokens.

    WARNING: This will invalidate all active download links.
    Use with caution, typically only for testing or emergency situations.
    """
    VALID_DOWNLOADS.clear()
    print("All download tokens cleared")
