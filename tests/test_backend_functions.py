#!/usr/bin/env python3
"""
Comprehensive backend function tester
Tests the actual backend functions step by step to debug fallback processing
"""

import sys
import os
import re
from pathlib import Path

# Add backend to Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)
sys.path.insert(0, os.path.dirname(__file__))

try:
    from docx import Document
    print("✅ python-docx imported successfully")
except ImportError:
    print("❌ python-docx not installed. Run: pip install python-docx")
    sys.exit(1)

def test_basic_text_extraction(doc_path: str):
    """Test basic text extraction that matches the backend"""
    print("\n1️⃣ Testing basic text extraction...")
    
    try:
        doc = Document(doc_path)
        all_paragraphs_text = []
        for p_obj in doc.paragraphs:
            if p_obj.text.strip():
                all_paragraphs_text.append(p_obj.text.strip())
        
        full_text = "\n".join(all_paragraphs_text)
        print(f"   ✅ Extracted {len(full_text)} characters")
        print(f"   📄 Content preview:\n{full_text[:400]}{'...' if len(full_text) > 400 else ''}")
        
        return full_text
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return ""

def test_requirement_detection_patterns(text: str):
    """Test requirement detection using multiple approaches"""
    print("\n2️⃣ Testing requirement detection patterns...")
    
    lines = text.split('\n')
    requirements = []
    
    # Pattern 1: Look for requirement keywords in sentences
    requirement_keywords = [
        'must', 'shall', 'required', 'mandatory', 'obligated',
        'prohibited', 'forbidden', 'not permitted', 'not allowed',
        'will', 'should', 'need to', 'have to'
    ]
    
    print(f"   🔍 Scanning {len(lines)} lines for requirement keywords...")
    
    for line_num, line in enumerate(lines, 1):
        line_clean = line.strip()
        if not line_clean:
            continue
            
        line_lower = line_clean.lower()
        
        # Check for requirement keywords
        found_keywords = []
        for keyword in requirement_keywords:
            if keyword in line_lower:
                found_keywords.append(keyword)
        
        if found_keywords:
            # Determine priority based on keywords
            priority = 1  # Default high priority
            req_type = "general"
            
            if any(word in line_lower for word in ['must', 'shall', 'required', 'mandatory']):
                req_type = "mandatory"
                priority = 1
            elif any(word in line_lower for word in ['prohibited', 'forbidden', 'not permitted']):
                req_type = "prohibited" 
                priority = 1
            elif any(word in line_lower for word in ['will', 'should']):
                req_type = "recommended"
                priority = 2
            
            # Extract section number if present
            section_match = re.match(r'^(\d+\.?\d*\.?\d*)', line_clean)
            section = section_match.group(1) if section_match else "unknown"
            
            requirements.append({
                'text': line_clean,
                'type': req_type,
                'priority': priority,
                'section': section,
                'line_number': line_num,
                'keywords_found': found_keywords
            })
            
            print(f"   ✅ Line {line_num}: [{req_type.upper()}] {found_keywords} -> {line_clean[:80]}{'...' if len(line_clean) > 80 else ''}")
    
    print(f"\n   📊 Found {len(requirements)} requirements using pattern matching")
    
    # Group by type
    by_type = {}
    for req in requirements:
        req_type = req['type']
        if req_type not in by_type:
            by_type[req_type] = []
        by_type[req_type].append(req)
    
    for req_type, reqs in by_type.items():
        print(f"   📋 {req_type}: {len(reqs)} requirements")
    
    return requirements

def test_backend_legal_processor(doc_path: str):
    """Test the actual backend legal processor functions"""
    print("\n3️⃣ Testing backend legal processor...")
    
    try:
        # Try to import and test the legal processor
        from legal_document_processor import (
            extract_fallback_requirements,
            generate_instructions_from_fallback,
            parse_legal_document
        )
        print("   ✅ Successfully imported legal_document_processor")
        
        # Test parse_legal_document
        print("   🔍 Testing parse_legal_document...")
        try:
            doc_structure = parse_legal_document(doc_path)
            print(f"   📊 Document structure: {len(doc_structure.sections)} sections")
            print(f"   📋 Title: {doc_structure.title}")
            print(f"   👥 Authors: {doc_structure.authors}")
        except Exception as e:
            print(f"   ⚠️  parse_legal_document error: {e}")
        
        # Test extract_fallback_requirements
        print("   🔍 Testing extract_fallback_requirements...")
        try:
            backend_requirements = extract_fallback_requirements(doc_path)
            print(f"   📊 Backend found {len(backend_requirements)} requirements")
            
            if backend_requirements:
                for i, req in enumerate(backend_requirements[:3]):
                    print(f"   📋 Req {i+1}: [{req.requirement_type}] {req.text[:80]}{'...' if len(req.text) > 80 else ''}")
                    print(f"       Section: {req.section}, Priority: {req.priority}")
            else:
                print("   ⚠️  Backend found no requirements - this is the problem!")
                
        except Exception as e:
            print(f"   ❌ extract_fallback_requirements error: {e}")
            import traceback
            print(f"   🔧 Full traceback:\n{traceback.format_exc()}")
        
        # Test generate_instructions_from_fallback
        print("   🔍 Testing generate_instructions_from_fallback...")
        try:
            instructions = generate_instructions_from_fallback(doc_path, "test context")
            print(f"   📝 Generated {len(instructions)} characters of instructions")
            print(f"   📄 Instructions preview: {instructions[:200]}{'...' if len(instructions) > 200 else ''}")
        except Exception as e:
            print(f"   ❌ generate_instructions_from_fallback error: {e}")
            
    except ImportError as e:
        print(f"   ❌ Could not import legal_document_processor: {e}")
        return False
    
    return True

def test_api_endpoint_simulation(doc_path: str):
    """Simulate what the API endpoint does"""
    print("\n4️⃣ Simulating API endpoint behavior...")
    
    try:
        # This simulates what /analyze-fallback-requirements/ does
        from legal_document_processor import extract_fallback_requirements
        from requirements_processor import process_fallback_document_requirements, generate_enhanced_instructions
        
        print("   🔍 Testing enhanced requirements processing...")
        
        try:
            # Try enhanced processing first (like the API does)
            instructions = generate_enhanced_instructions(doc_path, "test context")
            print(f"   ✅ Enhanced processing: {len(instructions)} characters")
        except Exception as e:
            print(f"   ⚠️  Enhanced processing failed: {e}")
            
            # Fallback to basic processing
            from legal_document_processor import generate_instructions_from_fallback
            instructions = generate_instructions_from_fallback(doc_path, "test context")
            print(f"   ✅ Basic processing fallback: {len(instructions)} characters")
        
        try:
            # Try detailed requirements processing
            processed_requirements = process_fallback_document_requirements(doc_path)
            print(f"   ✅ Processed requirements: {len(processed_requirements)}")
        except Exception as e:
            print(f"   ⚠️  Detailed requirements processing failed: {e}")
            
            # Use basic requirements
            requirements = extract_fallback_requirements(doc_path)
            print(f"   ✅ Basic requirements fallback: {len(requirements)}")
            
    except ImportError as e:
        print(f"   ❌ Could not import required modules: {e}")

def comprehensive_test(doc_path: str):
    """Run comprehensive test of fallback document processing"""
    
    if not os.path.exists(doc_path):
        print(f"❌ File not found: {doc_path}")
        return
    
    print(f"🔬 Comprehensive Backend Function Test")
    print(f"📄 Document: {doc_path}")
    print("=" * 70)
    
    # Test 1: Basic text extraction
    text = test_basic_text_extraction(doc_path)
    if not text:
        print("❌ Cannot proceed - text extraction failed")
        return
    
    # Test 2: Manual requirement detection
    manual_requirements = test_requirement_detection_patterns(text)
    
    # Test 3: Backend legal processor
    backend_success = test_backend_legal_processor(doc_path)
    
    # Test 4: API simulation
    if backend_success:
        test_api_endpoint_simulation(doc_path)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Summary:")
    print(f"   📄 Text extracted: {len(text)} characters")
    print(f"   🔍 Manual detection found: {len(manual_requirements)} requirements")
    
    if manual_requirements and not backend_success:
        print("   🚨 ISSUE: Manual detection works but backend doesn't!")
        print("   💡 The backend legal processor needs fixing")
    elif manual_requirements:
        print("   ✅ Both manual and backend detection should work")
    else:
        print("   ⚠️  Document may need more explicit requirement language")

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_backend_functions.py path/to/document.docx")
        print("\nThis script tests all the backend functions step by step")
        print("to identify exactly where the fallback processing is failing.")
        sys.exit(1)
    
    doc_path = sys.argv[1]
    comprehensive_test(doc_path)

if __name__ == "__main__":
    main()