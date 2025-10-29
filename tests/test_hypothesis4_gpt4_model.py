#!/usr/bin/env python3
"""
Hypothesis 4: Test if GPT-4 handles complex fallback better than gpt-5-mini

This script temporarily patches the extract_conditional_instructions_with_llm
function to use GPT-4 (gpt-4o deployment) instead of the default gpt-5-mini.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_gpt4_on_case02():
    """Test GPT-4 model on case_02 complex fallback"""

    # Import after path setup
    from backend.legal_document_processor import (
        extract_conditional_instructions_with_llm,
        get_llm_analysis
    )
    from backend.ai_client import get_chat_response

    # Path to fallback document
    fallback_path = "tests/golden_dataset/fallback_documents/c1_mock_fallBack.docx"

    if not os.path.exists(fallback_path):
        print(f"ERROR: Fallback document not found at {fallback_path}")
        return

    print("=" * 80)
    print("HYPOTHESIS 4: Testing GPT-4 vs gpt-5-mini on Complex Fallback")
    print("=" * 80)
    print(f"Test file: {fallback_path}")
    print()

    # Monkey-patch get_llm_analysis to use gpt-4o
    original_get_llm_analysis = get_llm_analysis

    def get_llm_analysis_gpt4(prompt: str, content: str, model: str = None) -> str:
        """Patched version that forces GPT-4"""
        try:
            messages = [
                {"role": "system", "content": "You are an expert legal document analyst."},
                {"role": "user", "content": f"{prompt}\n\nDocument content:\n{content}"}
            ]

            # Force GPT-4o model
            model_to_use = "gpt-4o"  # Try gpt-4o deployment
            print(f"🔧 [HYPOTHESIS 4] Forcing model: {model_to_use}")

            kwargs = {"temperature": 0.0, "seed": 42, "max_tokens": 2000, "model": model_to_use}

            return get_chat_response(messages, **kwargs)
        except Exception as e:
            print(f"Error in LLM analysis with GPT-4: {e}")
            print(f"Trying fallback to gpt-4 (without 'o')")
            try:
                # Try just "gpt-4" if "gpt-4o" doesn't work
                kwargs["model"] = "gpt-4"
                return get_chat_response(messages, **kwargs)
            except Exception as e2:
                print(f"Error with gpt-4 too: {e2}")
                return "{}"

    # Monkey-patch the module
    import backend.legal_document_processor as ldp_module
    ldp_module.get_llm_analysis = get_llm_analysis_gpt4

    try:
        print("Testing with GPT-4 model override...")
        print()

        instructions = extract_conditional_instructions_with_llm(fallback_path, context="")

        print()
        print("=" * 80)
        print("RESULTS")
        print("=" * 80)
        print(f"Instructions length: {len(instructions)} characters")
        print()

        if instructions and instructions.strip() and instructions.strip() not in ["", "No requirements found in fallback document."]:
            print("✅ GPT-4 generated instructions!")
            print()
            print("Instructions preview (first 500 chars):")
            print(instructions[:500])
            print()

            # Count number of instructions
            instruction_lines = [line for line in instructions.split('\n') if line.strip() and not line.strip().startswith('#')]
            numbered_instructions = [line for line in instruction_lines if line.strip() and line.strip()[0].isdigit()]
            print(f"Number of instructions generated: {len(numbered_instructions)}")
            print()
            print("Full instructions:")
            print(instructions)
        else:
            print("❌ GPT-4 did NOT generate instructions (empty or error)")
            print(f"Response: {instructions}")

    finally:
        # Restore original function
        ldp_module.get_llm_analysis = original_get_llm_analysis

    print()
    print("=" * 80)
    print("Test complete")
    print("=" * 80)

if __name__ == "__main__":
    test_gpt4_on_case02()
