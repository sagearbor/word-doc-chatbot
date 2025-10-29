#!/usr/bin/env python3
"""
Hypothesis 4 Comparison: Test both GPT-4 and gpt-5-mini side-by-side
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_both_models():
    """Test both gpt-5-mini (default) and GPT-4 on the same document"""

    from backend.legal_document_processor import extract_conditional_instructions_with_llm
    from backend.ai_client import get_chat_response
    import backend.legal_document_processor as ldp_module

    # Path to fallback document
    fallback_path = "tests/golden_dataset/fallback_documents/c1_mock_fallBack.docx"

    if not os.path.exists(fallback_path):
        print(f"ERROR: Fallback document not found at {fallback_path}")
        return

    print("=" * 80)
    print("HYPOTHESIS 4: GPT-4 vs gpt-5-mini Comparison")
    print("=" * 80)
    print(f"Test file: {fallback_path}")
    print()

    # Test 1: Default model (gpt-5-mini)
    print("TEST 1: Default model (gpt-5-mini)")
    print("-" * 80)

    instructions_default = extract_conditional_instructions_with_llm(fallback_path, context="")

    print(f"Instructions length: {len(instructions_default)} characters")
    if instructions_default and instructions_default.strip():
        instruction_lines = [line for line in instructions_default.split('\n') if line.strip() and not line.strip().startswith('#')]
        numbered_instructions = [line for line in instruction_lines if line.strip() and line.strip()[0].isdigit()]
        print(f"Number of instructions: {len(numbered_instructions)}")
        print(f"Preview: {instructions_default[:200]}")
    else:
        print("No instructions generated")
    print()

    # Test 2: GPT-4 model override
    print("TEST 2: GPT-4o model override")
    print("-" * 80)

    # Monkey-patch to force GPT-4
    original_get_llm_analysis = ldp_module.get_llm_analysis

    def get_llm_analysis_gpt4(prompt: str, content: str, model: str = None) -> str:
        """Patched version that forces GPT-4"""
        try:
            messages = [
                {"role": "system", "content": "You are an expert legal document analyst."},
                {"role": "user", "content": f"{prompt}\n\nDocument content:\n{content}"}
            ]

            model_to_use = "gpt-4o"
            print(f"🔧 Using model: {model_to_use}")

            kwargs = {"temperature": 0.0, "seed": 42, "max_tokens": 2000, "model": model_to_use}
            return get_chat_response(messages, **kwargs)
        except Exception as e:
            print(f"Error with GPT-4o: {e}")
            return "{}"

    ldp_module.get_llm_analysis = get_llm_analysis_gpt4

    try:
        instructions_gpt4 = extract_conditional_instructions_with_llm(fallback_path, context="")

        print(f"Instructions length: {len(instructions_gpt4)} characters")
        if instructions_gpt4 and instructions_gpt4.strip():
            instruction_lines = [line for line in instructions_gpt4.split('\n') if line.strip() and not line.strip().startswith('#')]
            numbered_instructions = [line for line in instruction_lines if line.strip() and line.strip()[0].isdigit()]
            print(f"Number of instructions: {len(numbered_instructions)}")
            print(f"Preview: {instructions_gpt4[:200]}")
        else:
            print("No instructions generated")

    finally:
        ldp_module.get_llm_analysis = original_get_llm_analysis

    print()
    print("=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)

    default_count = len([line for line in instructions_default.split('\n') if line.strip() and line.strip()[0].isdigit()]) if instructions_default else 0
    gpt4_count = len([line for line in instructions_gpt4.split('\n') if line.strip() and line.strip()[0].isdigit()]) if instructions_gpt4 else 0

    print(f"gpt-5-mini instructions: {default_count}")
    print(f"GPT-4o instructions: {gpt4_count}")
    print()

    if gpt4_count > default_count:
        print(f"✅ HYPOTHESIS 4 CONFIRMED: GPT-4o generates MORE instructions ({gpt4_count} vs {default_count})")
        print("   GPT-4o is more capable of understanding the complex fallback document.")
    elif gpt4_count == default_count:
        print(f"⚖️  HYPOTHESIS 4 INCONCLUSIVE: Both models generate same number of instructions ({gpt4_count})")
    else:
        print(f"❌ HYPOTHESIS 4 NOT CONFIRMED: gpt-5-mini generates more instructions ({default_count} vs {gpt4_count})")

    print()
    print("Full gpt-5-mini output:")
    print(instructions_default)
    print()
    print("Full GPT-4o output:")
    print(instructions_gpt4)

if __name__ == "__main__":
    test_both_models()
