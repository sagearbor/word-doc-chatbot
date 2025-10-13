#!/usr/bin/env python3
"""
Test script for comparative analysis functionality
"""

import requests
import json
import sys
import os

# Enable comparative analysis
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from backend.legal_document_processor import enable_comparative_analysis, get_current_mode

print("🔄 Enabling comparative analysis...")
enable_comparative_analysis()
print("📊 Current mode:", get_current_mode())

# Test with c1 files
print("\n🧪 Testing comparative analysis with c1 files...")

url = "http://localhost:8888/process-document-with-fallback/"

files = {
    'input_file': open('tests/golden_dataset/input_documents/c1_fromPharma_MOCK_DCRI_Northstar_Therapeutics_PhaseII_Contract - Copy.docx', 'rb'),
    'fallback_file': open('tests/golden_dataset/fallback_documents/c1_fallBack_MOCK_DCRI_Northstar_Therapeutics_PhaseII_Contract.docx', 'rb')
}

data = {
    'user_instructions': 'Apply all requirements from the fallback document using comparative analysis',
    'merge_strategy': 'priority'
}

try:
    print("📤 Sending request to backend...")
    response = requests.post(url, files=files, data=data, timeout=120)
    
    print(f"📨 Response status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success! Processing completed")
        print(f"📈 Changes applied: {result.get('changes_applied', 'N/A')}")
        print(f"📋 Success rate: {result.get('success_rate', 'N/A')}")
        print(f"📝 Summary: {result.get('summary', 'N/A')[:200]}...")
        
        if result.get('debug_info'):
            print("\n🔍 Debug info:")
            debug = result['debug_info']
            if 'processing_log' in debug:
                log_lines = debug['processing_log'].split('\n')[-10:]  # Last 10 lines
                for line in log_lines:
                    if 'comparative' in line.lower() or 'comparison' in line.lower():
                        print(f"  📌 {line}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
except Exception as e:
    print(f"❌ Request failed: {e}")

finally:
    files['input_file'].close()
    files['fallback_file'].close()