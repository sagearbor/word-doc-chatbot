#!/usr/bin/env python3
"""
Test script to verify complex fallback document processing works correctly.
Run this tomorrow to validate the fallback processing improvements.
"""

import pytest
import requests
import os
import sys
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

def test_complex_fallback_processing():
    """
    Test that complex fallback document generates multiple edits
    and applies them successfully.
    """
    
    # Backend URL
    BACKEND_URL = "http://127.0.0.1:8000"
    
    # File paths
    main_doc = "test_main_document.docx"
    complex_fallback = "test_complex_fallback.docx"
    
    # Verify files exist
    assert os.path.exists(main_doc), f"Main document {main_doc} not found. Run create_test_documents.py first."
    assert os.path.exists(complex_fallback), f"Complex fallback {complex_fallback} not found. Run create_test_documents.py first."
    
    # Prepare files for upload
    with open(main_doc, 'rb') as main_f, open(complex_fallback, 'rb') as fallback_f:
        files = {
            'input_file': ('main.docx', main_f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
            'fallback_file': ('fallback.docx', fallback_f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        }
        
        data = {
            'user_instructions': '',
            'author_name': 'Test Author',
            'case_sensitive': True,
            'add_comments': True,
            'debug_mode': True,
            'extended_debug_mode': True,
            'merge_strategy': 'append'
        }
        
        # Make the API call
        response = requests.post(
            f"{BACKEND_URL}/process-document-with-fallback/", 
            files=files, 
            data=data,
            timeout=120
        )
    
    # Verify API call succeeded
    assert response.status_code == 200, f"API call failed: {response.status_code} - {response.text}"
    
    result = response.json()
    
    # Verify multiple edits were generated and applied
    edits_suggested = result.get('edits_suggested_count', 0)
    edits_applied = result.get('edits_applied_count', 0)
    
    print(f"✅ Complex fallback test results:")
    print(f"   📊 Edits suggested: {edits_suggested}")
    print(f"   ✅ Edits applied: {edits_applied}")
    print(f"   📝 Success rate: {edits_applied}/{edits_suggested} ({edits_applied/edits_suggested*100:.1f}%)")
    
    # Assertions for success
    assert edits_suggested >= 5, f"Expected at least 5 edits from complex fallback, got {edits_suggested}"
    assert edits_applied >= 3, f"Expected at least 3 edits to be applied, got {edits_applied}"
    assert edits_applied/edits_suggested >= 0.5, f"Success rate too low: {edits_applied}/{edits_suggested}"
    
    # Verify debug information is present
    debug_info = result.get('debug_info', {})
    assert debug_info, "Debug information should be present"
    
    extended_details = debug_info.get('extended_details', {})
    fallback_analysis = extended_details.get('fallback_document_analysis', {})
    
    if isinstance(fallback_analysis, dict):
        requirements_count = fallback_analysis.get('fallback_requirements_count', 0)
        assert requirements_count >= 5, f"Expected at least 5 requirements from complex fallback, got {requirements_count}"
        print(f"   📋 Requirements extracted: {requirements_count}")
    else:
        print(f"   ⚠️  Fallback analysis format: {type(fallback_analysis)}")
    
    print(f"✅ Complex fallback processing test PASSED!")
    
    return result

def test_simple_vs_complex_fallback():
    """
    Compare simple and complex fallback documents to ensure 
    complex generates more edits.
    """
    # This would compare test_fallback_requirements.docx vs test_complex_fallback.docx
    # and verify that complex generates more edits
    pass

if __name__ == "__main__":
    print("🧪 Testing Complex Fallback Document Processing...")
    print("=" * 60)
    
    try:
        # Check if backend is running
        response = requests.get("http://127.0.0.1:8000/", timeout=5)
        print("✅ Backend is running")
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running. Please start it first:")
        print("   python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    try:
        result = test_complex_fallback_processing()
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)