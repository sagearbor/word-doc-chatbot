#!/usr/bin/env python3
"""
Debug script to capture and display LLM calls for case_02
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from legal_document_processor import generate_instructions_from_fallback
from main import extract_text_for_llm

# Paths
case_dir = Path(__file__).parent / "test_cases" / "case_02_contract_editing"
input_file = case_dir / "input" / "case_02_input_service_agreement.docx"
fallback_file = case_dir / "fallback" / "case_02_fallback_comprehensive_guidelines.docx"

print("="*80)
print("DEBUGGING CASE 02 - LLM CALL ANALYSIS")
print("="*80)

# Step 1: Extract text from input document
print("\n📄 STEP 1: Extract text from input document")
print("-"*80)
input_text = extract_text_for_llm(str(input_file))
print(f"Input document text ({len(input_text)} chars):")
print(input_text)
print()

# Step 2: Generate instructions from fallback document (AI CALL #1)
print("\n🧠 STEP 2: Generate instructions from fallback (AI CALL #1)")
print("-"*80)
print("Calling generate_instructions_from_fallback()...")
print()

fallback_instructions = generate_instructions_from_fallback(
    str(fallback_file),
    context=f"Processing {input_file.name} with fallback requirements"
)

print(f"\n✅ AI Call #1 Generated Instructions ({len(fallback_instructions)} chars):")
print("="*80)
print(fallback_instructions)
print("="*80)

# Step 3: Show what would be sent to AI Call #2
print("\n📤 STEP 3: What AI Call #2 would receive")
print("-"*80)
print(f"Main document text: {input_text[:500]}...")
print(f"\nInstructions from AI Call #1: {fallback_instructions[:500]}...")
print()

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
print("\nNext: AI Call #2 would receive:")
print("  - Document: case_02_input_service_agreement.docx")
print("  - Text: (115 words shown above)")
print("  - Instructions: (from AI Call #1 shown above)")
print("\nAI Call #2 should generate edits that:")
print("  1. Find text in the input document")
print("  2. Modify it according to fallback requirements")
print("  3. Handle missing requirements by finding related text")
