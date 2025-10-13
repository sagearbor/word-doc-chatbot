#!/usr/bin/env python3
"""
Test script to compare LLM-based vs regex-based requirement extraction
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.legal_document_processor import (
    generate_instructions_from_fallback,
    enable_full_llm_mode,
    disable_full_llm_mode,
    get_current_mode
)

def test_both_approaches(fallback_doc_path):
    """Test both regex and LLM approaches on the same document"""
    
    if not os.path.exists(fallback_doc_path):
        print(f"Error: Fallback document not found: {fallback_doc_path}")
        return
    
    print("=" * 60)
    print(f"TESTING DOCUMENT: {os.path.basename(fallback_doc_path)}")
    print("=" * 60)
    
    # Test 1: Regex-based approach (current default)
    print("\n1. REGEX-BASED APPROACH (Default)")
    print("-" * 40)
    disable_full_llm_mode()  # Ensure we're using regex
    print(f"Mode: {get_current_mode()}")
    print()
    
    try:
        regex_instructions = generate_instructions_from_fallback(fallback_doc_path)
        print("REGEX INSTRUCTIONS:")
        print(regex_instructions)
    except Exception as e:
        print(f"Error with regex approach: {e}")
        regex_instructions = None
    
    print("\n" + "=" * 60)
    
    # Test 2: LLM-based approach
    print("\n2. LLM-BASED APPROACH (Intelligent)")
    print("-" * 40)
    enable_full_llm_mode()  # Enable LLM for both extraction and instructions
    print(f"Mode: {get_current_mode()}")
    print()
    
    try:
        llm_instructions = generate_instructions_from_fallback(fallback_doc_path)
        print("LLM INSTRUCTIONS:")
        print(llm_instructions)
    except Exception as e:
        print(f"Error with LLM approach: {e}")
        llm_instructions = None
    
    print("\n" + "=" * 60)
    
    # Comparison
    print("\n3. COMPARISON")
    print("-" * 40)
    if regex_instructions and llm_instructions:
        regex_count = len([line for line in regex_instructions.split('\n') if line.strip() and line[0].isdigit()])
        llm_count = len([line for line in llm_instructions.split('\n') if line.strip() and line[0].isdigit()])
        
        print(f"Regex approach generated: {regex_count} instructions")
        print(f"LLM approach generated: {llm_count} instructions")
        
        if llm_count > regex_count:
            print("✅ LLM found more requirements than regex")
        elif regex_count > llm_count:
            print("⚠️  Regex found more requirements than LLM")
        else:
            print("📊 Both approaches found the same number of requirements")
    
    # Reset to default
    disable_full_llm_mode()

if __name__ == "__main__":
    # Look for test documents
    test_docs = [
        "debug_word_processor/document.xml",  # This might not be a .docx
        "test_fallback_document.docx",  # This might exist from previous tests
    ]
    
    # Try to find an existing test document
    found_doc = None
    for doc in test_docs:
        if os.path.exists(doc):
            found_doc = doc
            break
    
    if found_doc:
        test_both_approaches(found_doc)
    else:
        print("No test documents found. Available test documents should be:")
        for doc in test_docs:
            print(f"  - {doc}")
        print()
        print("To run this test:")
        print("1. Make sure you have a fallback document (.docx file)")
        print("2. Run: python test_llm_approach.py")
        print("3. Or call test_both_approaches('path/to/your/fallback.docx')")
        
        # Show current mode
        print(f"\nCurrent mode: {get_current_mode()}")