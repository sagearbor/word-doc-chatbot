"""
Centralized secure error handling module.

This module provides secure error handling that:
- Prevents information leakage in error messages
- Logs full error details server-side for debugging
- Provides unique error IDs for correlation
- Distinguishes between development and production environments
- Filters sensitive data from error messages

SECURITY NOTE: Never expose internal implementation details, file paths,
or stack traces to end users in production.
"""
import os
import secrets
import logging
import traceback
from typing import Optional
from fastapi import HTTPException


# Configure logger
logger = logging.getLogger(__name__)


def generate_error_id() -> str:
    """
    Generate a unique error ID for correlation between user reports and server logs.

    Returns:
        Cryptographically secure random error ID
    """
    return secrets.token_urlsafe(16)


def handle_error(
    e: Exception,
    context: str,
    status_code: int = 500,
    include_details_in_response: bool = False
) -> HTTPException:
    """
    Centralized error handling with secure logging.

    This function:
    - Generates a unique error ID for tracking
    - Logs full error details server-side (including stack trace)
    - Returns sanitized error message to user (no sensitive details)
    - Respects ENVIRONMENT setting (more verbose in development)

    Args:
        e: The exception that occurred
        context: Context description (e.g., "processing document", "analyzing file")
        status_code: HTTP status code (default 500)
        include_details_in_response: Override to include exception type (use carefully)

    Returns:
        HTTPException with safe error message and unique error ID

    Example:
        try:
            process_document(file)
        except HTTPException:
            raise  # Re-raise HTTP exceptions as-is
        except Exception as e:
            raise handle_error(e, "document processing")
    """
    error_id = generate_error_id()

    # Log full details server-side (including stack trace)
    logger.error(
        f"Error ID {error_id} - Context: {context} - Exception: {type(e).__name__}: {str(e)}",
        exc_info=True
    )

    # Determine environment
    is_development = os.getenv("ENVIRONMENT") == "development"

    # Prepare user-facing message (no sensitive details)
    if is_development and include_details_in_response:
        # In development, can include sanitized error type
        user_message = f"Error during {context}: {type(e).__name__}. Error ID: {error_id}"
    else:
        # In production, generic message only
        user_message = f"An error occurred during {context}. Please contact support with Error ID: {error_id}"

    return HTTPException(status_code=status_code, detail=user_message)


def handle_validation_error(field: str, message: str) -> HTTPException:
    """
    Handle validation errors with clear messaging.

    Args:
        field: The field that failed validation
        message: Validation error message

    Returns:
        HTTPException with status 400 (Bad Request)
    """
    return HTTPException(
        status_code=400,
        detail=f"Validation error for {field}: {message}"
    )


def handle_not_found(resource: str, identifier: Optional[str] = None) -> HTTPException:
    """
    Handle resource not found errors.

    Args:
        resource: Type of resource (e.g., "file", "document", "token")
        identifier: Optional identifier (will be sanitized)

    Returns:
        HTTPException with status 404 (Not Found)
    """
    if identifier:
        # Sanitize identifier to prevent information leakage
        safe_id = identifier[:20] + "..." if len(identifier) > 20 else identifier
        detail = f"{resource.capitalize()} not found: {safe_id}"
    else:
        detail = f"{resource.capitalize()} not found"

    return HTTPException(status_code=404, detail=detail)


def handle_forbidden(reason: Optional[str] = None) -> HTTPException:
    """
    Handle forbidden access errors.

    Args:
        reason: Optional reason (keep generic to avoid information leakage)

    Returns:
        HTTPException with status 403 (Forbidden)
    """
    detail = reason if reason else "Access denied"
    return HTTPException(status_code=403, detail=detail)


def handle_rate_limit_exceeded(retry_after: Optional[int] = None) -> HTTPException:
    """
    Handle rate limit exceeded errors.

    Args:
        retry_after: Seconds until the rate limit resets

    Returns:
        HTTPException with status 429 (Too Many Requests)
    """
    if retry_after:
        detail = f"Rate limit exceeded. Please try again in {retry_after} seconds."
    else:
        detail = "Rate limit exceeded. Please try again later."

    headers = {"Retry-After": str(retry_after)} if retry_after else {}

    return HTTPException(status_code=429, detail=detail, headers=headers)


class SensitiveDataFilter(logging.Filter):
    """
    Logging filter to redact sensitive data from log messages.

    This filter should be applied to all log handlers to prevent
    accidental logging of sensitive information.
    """

    SENSITIVE_PATTERNS = [
        # API keys and tokens
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?([^\s"\']+)', r'api_key=REDACTED'),
        (r'bearer\s+([a-zA-Z0-9\-_.]+)', r'bearer REDACTED'),
        (r'sk-[a-zA-Z0-9]{48}', r'sk-REDACTED'),  # OpenAI API keys

        # Credentials
        (r'password["\']?\s*[:=]\s*["\']?([^\s"\']+)', r'password=REDACTED'),
        (r'secret["\']?\s*[:=]\s*["\']?([^\s"\']+)', r'secret=REDACTED'),

        # PII
        (r'\d{3}-\d{2}-\d{4}', r'XXX-XX-XXXX'),  # SSN
        (r'\d{16}', r'XXXX-XXXX-XXXX-XXXX'),  # Credit card
    ]

    def filter(self, record):
        """Filter log records to redact sensitive data."""
        import re

        if isinstance(record.msg, str):
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                record.msg = re.sub(pattern, replacement, record.msg, flags=re.IGNORECASE)

        return True


def setup_secure_logging():
    """
    Setup secure logging configuration with sensitive data filtering.

    This should be called during application startup to ensure all logs
    are properly filtered.
    """
    # Add sensitive data filter to all handlers
    for handler in logging.root.handlers:
        handler.addFilter(SensitiveDataFilter())

    logger.info("Secure logging configured with sensitive data filtering")


def debug_log(message: str, sensitive: bool = False):
    """
    Log debug message only if in development mode.

    Args:
        message: The message to log
        sensitive: If True, truncates message to avoid logging too much data
    """
    if os.getenv("ENVIRONMENT") == "development":
        if sensitive:
            # Truncate sensitive data
            safe_message = message[:100] + "..." if len(message) > 100 else message
            logger.debug(f"[SENSITIVE] {safe_message}")
        else:
            logger.debug(message)


def get_error_stats() -> dict:
    """
    Get error statistics (useful for monitoring).

    Returns:
        Dictionary containing error statistics
    """
    # In a production system, this would query a metrics database
    # For now, return a placeholder
    return {
        "error_tracking_enabled": True,
        "environment": os.getenv("ENVIRONMENT", "unknown")
    }
