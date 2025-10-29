#!/usr/bin/env python3
"""
Test Hypothesis 3: LLM Correctly Returns Empty with Reason

This script tests if the LLM intentionally returns empty because it doesn't understand the task.
With the modified prompt, we force the LLM to explain itself if it can't find instructions.
"""

import os
import sys
from pathlib import Path

# Add project root to path so backend can be imported as a package
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now import from backend package (not standalone)
from backend.legal_document_processor import (
    extract_conditional_instructions_with_llm,
    extract_document_with_comments_and_changes
)

def test_hypothesis3():
    """Test Hypothesis 3: LLM returns empty with explanation"""

    print("=" * 80)
    print("HYPOTHESIS 3 TEST: LLM Understanding and Response Analysis")
    print("=" * 80)
    print()

    # Path to case_02 fallback document
    fallback_path = "/dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot/tests/golden_dataset/fallback_documents/c2_mock_fallback_rweRegistry.docx"

    if not os.path.exists(fallback_path):
        print(f"ERROR: Fallback document not found at {fallback_path}")
        return

    print(f"Testing with: {Path(fallback_path).name}")
    print()

    # Step 1: Show what's in the fallback document
    print("STEP 1: Extracting fallback document content...")
    print("-" * 80)
    try:
        full_content = extract_document_with_comments_and_changes(fallback_path)
        print(f"Document content length: {len(full_content)} characters")
        print()
        print("Document content preview:")
        print(full_content[:1000])
        print("...")
        print()
    except Exception as e:
        print(f"ERROR extracting content: {e}")
        return

    # Step 2: Call the modified function with the new prompt
    print("STEP 2: Calling extract_conditional_instructions_with_llm()...")
    print("-" * 80)
    print("This will use the MODIFIED prompt that requires a response")
    print()

    try:
        instructions = extract_conditional_instructions_with_llm(fallback_path, context="")

        print()
        print("=" * 80)
        print("RESULTS OF HYPOTHESIS 3 TEST")
        print("=" * 80)
        print()

        print(f"Instructions returned: {bool(instructions)}")
        print(f"Instructions length: {len(instructions) if instructions else 0} characters")
        print()

        if instructions:
            print("FULL INSTRUCTIONS RETURNED BY LLM:")
            print("-" * 80)
            print(instructions)
            print("-" * 80)
            print()

            # Analyze the response
            if "NO_INSTRUCTIONS_FOUND:" in instructions:
                print("✓ LLM EXPLAINED WHY IT FOUND NOTHING!")
                print()
                print("This suggests the LLM IS processing the request but genuinely")
                print("cannot find instructions in the fallback document.")
                print()
                print("The problem is NOT a technical issue but the LLM's understanding")
                print("of what to extract from the fallback document.")
            else:
                print("✓ LLM RETURNED INSTRUCTIONS!")
                print()
                print("This suggests the modified prompt helped the LLM understand")
                print("what to do. The previous empty responses may have been due to")
                print("unclear expectations in the prompt.")
        else:
            print("✗ LLM STILL RETURNED EMPTY!")
            print()
            print("Even with the explicit requirement to respond, the LLM returned empty.")
            print("This suggests a technical issue in the LLM call chain, NOT a prompt issue.")
            print()
            print("Check the logs at /tmp/llm_response_hypothesis1.txt for details.")

        print()

        # Check the detailed log file
        log_path = "/tmp/llm_response_hypothesis1.txt"
        if os.path.exists(log_path):
            print("DETAILED LLM RESPONSE LOG:")
            print("-" * 80)
            with open(log_path, 'r') as f:
                print(f.read())

    except Exception as e:
        print(f"ERROR during testing: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_hypothesis3()
