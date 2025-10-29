"""
Input sanitization module for LLM prompts.

This module protects against prompt injection attacks and other malicious inputs
that could manipulate LLM behavior or extract sensitive information.

SECURITY NOTE: All user inputs sent to LLMs should be sanitized using these functions.
"""
import re
import html
import os
from typing import Tuple, Optional


def sanitize_llm_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize input before sending to LLM to prevent injection attacks.

    This function:
    - Truncates text to reasonable length
    - Removes common prompt injection patterns
    - Escapes HTML/XML special characters
    - Removes excessive newlines (context manipulation)

    Args:
        text: The text to sanitize
        max_length: Maximum allowed length (default 10000 characters)

    Returns:
        Sanitized text safe for LLM processing
    """
    if not text:
        return ""

    # Truncate to reasonable length
    text = text[:max_length]

    # Remove potential prompt injection patterns
    injection_patterns = [
        # Common injection attempts
        r'(?i)(ignore|disregard|forget)\s+(all\s+)?(previous|prior|above)\s+instructions',
        r'(?i)system\s*:',
        r'(?i)you\s+are\s+now',
        r'(?i)new\s+instructions',
        r'(?i)debug\s+mode',
        r'(?i)admin\s+mode',
        r'(?i)override\s+instructions',

        # Special tokens that could manipulate LLM behavior
        r'<\|im_start\|>',
        r'<\|im_end\|>',
        r'<\|system\|>',
        r'<\|user\|>',
        r'<\|assistant\|>',
        r'<\|endoftext\|>',

        # Role manipulation attempts
        r'(?i)act\s+as\s+(admin|system|root)',
        r'(?i)pretend\s+you\s+are',
    ]

    for pattern in injection_patterns:
        text = re.sub(pattern, '[FILTERED]', text, flags=re.IGNORECASE)

    # Escape HTML/XML special characters
    text = html.escape(text)

    # Remove excessive newlines (potential for context manipulation)
    text = re.sub(r'\n{5,}', '\n\n', text)

    # Remove null bytes
    text = text.replace('\x00', '')

    return text


def validate_user_instructions(instructions: str) -> Tuple[bool, Optional[str]]:
    """
    Validate user instructions before processing.

    Checks for:
    - Empty or whitespace-only instructions
    - Excessive length
    - Suspicious patterns that indicate prompt injection

    Args:
        instructions: User-provided instructions

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
        - (True, None) if instructions are valid
        - (False, "error message") if instructions are invalid
    """
    if not instructions or not instructions.strip():
        return False, "Instructions cannot be empty."

    if len(instructions) > 5000:
        return False, "Instructions exceed maximum length of 5000 characters."

    # Check for suspicious patterns
    suspicious_patterns = [
        (r'system\s*:', "Instructions cannot contain system directives."),
        (r'\}\s*,\s*\{.*\}', "Instructions contain suspicious JSON-like structures."),
        (r'<\|.*?\|>', "Instructions contain invalid special tokens."),
        (r'(?i)reveal.*prompt', "Instructions contain suspicious content."),
        (r'(?i)show.*instructions', "Instructions contain suspicious content."),
    ]

    for pattern, error_msg in suspicious_patterns:
        if re.search(pattern, instructions, re.IGNORECASE):
            return False, error_msg

    return True, None


def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """
    Sanitize filename to prevent path traversal and other attacks.

    Args:
        filename: Original filename
        max_length: Maximum allowed length

    Returns:
        Sanitized filename safe for use
    """
    if not filename:
        return "unnamed"

    # Get basename only (remove any path components)
    filename = os.path.basename(filename)

    # Remove null bytes
    filename = filename.replace('\x00', '')

    # Remove or replace suspicious characters
    filename = re.sub(r'[<>:"|?*\\\/]', '_', filename)

    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')

    # Truncate to max length
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        if ext:
            max_name_len = max_length - len(ext)
            filename = name[:max_name_len] + ext
        else:
            filename = filename[:max_length]

    # Ensure filename is not empty after sanitization
    if not filename:
        return "unnamed"

    return filename


def validate_json_structure(json_str: str, max_items: int = 100) -> Tuple[bool, Optional[str]]:
    """
    Validate JSON structure from LLM responses.

    Args:
        json_str: JSON string to validate
        max_items: Maximum number of items allowed in arrays

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    import json

    try:
        data = json.loads(json_str)

        # Check if it's a list
        if isinstance(data, list):
            if len(data) > max_items:
                return False, f"JSON array exceeds maximum size of {max_items} items."

            # Check each item
            for item in data:
                if not isinstance(item, dict):
                    return False, "Invalid JSON structure: array items must be objects."

        return True, None

    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {str(e)}"
    except Exception as e:
        return False, f"Error validating JSON: {str(e)}"


def get_sanitization_config() -> dict:
    """
    Get current sanitization configuration.

    Returns:
        Dictionary containing sanitization settings
    """
    return {
        "max_input_length": 10000,
        "max_instructions_length": 5000,
        "max_filename_length": 100,
        "max_json_items": 100
    }
