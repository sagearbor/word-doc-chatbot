#!/usr/bin/env python3
"""
Hypothesis 2 Test: Apply Simple Prompt to legal_document_processor.py

This script modifies the extract_conditional_instructions_with_llm() function
to use a MUCH simpler prompt to test if prompt complexity/length is causing LLM timeouts.
"""

import re
import sys
from pathlib import Path

def apply_simple_prompt():
    """Apply simple prompt modification to legal_document_processor.py"""

    # Path to the file
    file_path = Path(__file__).parent.parent / "backend" / "legal_document_processor.py"

    print(f"Reading file: {file_path}")

    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()

    # Find the prompt definition section
    # Look for the line: prompt = f"""You are a legal document analysis expert

    # Pattern to match the entire prompt assignment
    prompt_pattern = r'(        # Specialized prompt for extracting conditional analysis instructions\s+prompt = f""".*?""")'

    # Check if we can find the pattern
    if not re.search(prompt_pattern, content, re.DOTALL):
        print("ERROR: Could not find the prompt section to replace!")
        # Try alternate pattern
        prompt_pattern = r'(        prompt = f"""You are a legal document analysis expert.*?Return ONLY the numbered instructions OR your NO_INSTRUCTIONS_FOUND explanation, nothing else.\s+""")'
        if not re.search(prompt_pattern, content, re.DOTALL):
            print("ERROR: Could not find alternate pattern either!")
            return False

    # New simple prompt code
    new_prompt_code = '''        # ORIGINAL COMPLEX PROMPT (SAVED FOR REFERENCE - Hypothesis 2)
        # original_prompt = f"""You are a legal document analysis expert. Your task is to analyze this fallback document and create specific analysis instructions that will be used to examine a main document.
        #
        # FALLBACK DOCUMENT CONTENT:
        # {full_content}
        #
        # TASK:
        # Extract all conditional rules, requirements, and analysis instructions from this fallback document. You MUST handle TWO types of changes:
        #
        # **TYPE A: TEXT REPLACEMENTS** (when fallback specifies exact text to replace)
        # **TYPE B: NEW REQUIREMENTS** (when fallback adds entirely new clauses/requirements)
        #
        # ... [rest of complex prompt]
        # """

        # HYPOTHESIS 2: MUCH SIMPLER PROMPT
        # Test if simpler prompt gets any response at all
        content_preview = full_content[:1000] if len(full_content) > 1000 else full_content

        prompt = f"""Read this fallback document and extract all requirements as numbered instructions.

Fallback document (first 1000 chars):
{content_preview}

Return only numbered instructions (e.g., "1. Change X to Y"), nothing else."""

        print(f"📏 HYPOTHESIS 2: Using SIMPLE prompt")
        print(f"   - Prompt length: {len(prompt)} characters (vs ~2700 original)")
        print(f"   - Content chars: {len(content_preview)} (vs {len(full_content)} full)")'''

    # Replace the prompt section
    modified_content = re.sub(prompt_pattern, new_prompt_code, content, count=1, flags=re.DOTALL)

    # Check if replacement worked
    if modified_content == content:
        print("ERROR: No replacement occurred!")
        return False

    # Write the modified content back
    backup_path = file_path.with_suffix('.py.backup_hypothesis2')
    print(f"Creating backup: {backup_path}")
    with open(backup_path, 'w') as f:
        f.write(content)

    print(f"Writing modified file: {file_path}")
    with open(file_path, 'w') as f:
        f.write(modified_content)

    print("✅ Successfully applied simple prompt modification!")
    print("\nNext steps:")
    print("1. Run: pytest tests/debug_case_02_llm_calls.py -v -s")
    print("2. Check logs for 'HYPOTHESIS 2: Using SIMPLE prompt'")
    print("3. See if LLM returns any response at all")
    print("4. If it works, gradually add complexity to find breaking point")

    return True

if __name__ == "__main__":
    success = apply_simple_prompt()
    sys.exit(0 if success else 1)
