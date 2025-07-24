#!/usr/bin/env python3
"""
Debug script for testing fallback document processing
Usage: python debug_fallback.py path/to/your/fallback.docx
"""

import sys
import os
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from backend.legal_document_processor import (
        extract_fallback_requirements, 
        generate_instructions_from_fallback,
        parse_legal_document
    )
    from backend.main import extract_text_for_llm
    print("✅ Successfully imported backend functions")
except ImportError as e:
    print(f"❌ Import error: {e}")
    try:
        # Fallback: try to import directly and define basic text extraction
        from backend.legal_document_processor import (
            extract_fallback_requirements, 
            generate_instructions_from_fallback,
            parse_legal_document
        )
        from docx import Document
        
        def extract_text_for_llm(path: str) -> str:
            """Simple fallback text extraction"""
            try:
                doc = Document(path)
                return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            except Exception as e:
                return f"Error extracting text: {e}"
        
        print("✅ Using fallback text extraction")
    except ImportError as e2:
        print(f"❌ Fallback import also failed: {e2}")
        print("Make sure you're running this from the project root directory")
        print("And that all required packages are installed: pip install -r requirements.txt")
        sys.exit(1)

def debug_fallback_document(doc_path: str):
    """Debug fallback document processing step by step"""
    
    if not os.path.exists(doc_path):
        print(f"❌ File not found: {doc_path}")
        return
    
    if not doc_path.lower().endswith('.docx'):
        print("❌ File must be a .docx file")
        return
    
    print(f"🔍 Analyzing fallback document: {doc_path}")
    print("=" * 60)
    
    # Step 1: Extract basic text
    print("\n1️⃣ Extracting basic document text...")
    try:
        basic_text = extract_text_for_llm(doc_path)
        print(f"   ✅ Extracted {len(basic_text)} characters of text")
        print(f"   📝 First 200 chars: {basic_text[:200]}...")
        if len(basic_text) == 0:
            print("   ⚠️  WARNING: No text extracted from document!")
    except Exception as e:
        print(f"   ❌ Error extracting text: {e}")
        return
    
    # Step 2: Parse legal document structure
    print("\n2️⃣ Parsing legal document structure...")
    try:
        doc_structure = parse_legal_document(doc_path)
        print(f"   ✅ Found document title: {doc_structure.title}")
        print(f"   📊 Sections found: {len(doc_structure.sections)}")
        print(f"   📊 Whereas clauses: {len(doc_structure.whereas_clauses)}")
        print(f"   👥 Authors: {doc_structure.authors}")
        
        if doc_structure.sections:
            print("   📋 Section previews:")
            for i, section in enumerate(doc_structure.sections[:3]):  # Show first 3
                print(f"      {section.number}: {section.title[:50]}{'...' if len(section.title) > 50 else ''}")
            if len(doc_structure.sections) > 3:
                print(f"      ... and {len(doc_structure.sections) - 3} more sections")
                
    except Exception as e:
        print(f"   ❌ Error parsing document structure: {e}")
        print(f"   🔧 Continuing with basic requirements extraction...")
    
    # Step 3: Extract requirements
    print("\n3️⃣ Extracting fallback requirements...")
    try:
        requirements = extract_fallback_requirements(doc_path)
        print(f"   ✅ Extracted {len(requirements)} requirements")
        
        if requirements:
            print("   📋 Requirements breakdown:")
            
            # Group by type
            by_type = {}
            for req in requirements:
                req_type = req.requirement_type
                if req_type not in by_type:
                    by_type[req_type] = []
                by_type[req_type].append(req)
            
            for req_type, reqs in by_type.items():
                print(f"      {req_type}: {len(reqs)} requirements")
            
            # Show priority distribution
            by_priority = {}
            for req in requirements:
                priority = req.priority
                if priority not in by_priority:
                    by_priority[priority] = 0
                by_priority[priority] += 1
            
            print(f"   📊 Priority distribution:")
            for priority in sorted(by_priority.keys()):
                print(f"      Priority {priority}: {by_priority[priority]} requirements")
            
            # Show first few requirements
            print(f"\n   📝 Sample requirements:")
            for i, req in enumerate(requirements[:3]):
                print(f"      {i+1}. [{req.requirement_type.upper()}] {req.text[:100]}{'...' if len(req.text) > 100 else ''}")
                print(f"         Section: {req.section}, Priority: {req.priority}")
            
            if len(requirements) > 3:
                print(f"      ... and {len(requirements) - 3} more requirements")
                
        else:
            print("   ⚠️  No requirements found in document!")
            print("   💡 This might be because:")
            print("      - Document doesn't contain requirement language (must, shall, required, etc.)")
            print("      - Document format is not recognized as legal text")
            print("      - Document is empty or corrupted")
        
    except Exception as e:
        print(f"   ❌ Error extracting requirements: {e}")
        import traceback
        print(f"   🔧 Full error: {traceback.format_exc()}")
    
    # Step 4: Generate instructions
    print("\n4️⃣ Generating LLM instructions...")
    try:
        instructions = generate_instructions_from_fallback(doc_path, "Debug test context")
        print(f"   ✅ Generated {len(instructions)} characters of instructions")
        print(f"   📝 Instructions preview:")
        print(f"      {instructions[:300]}{'...' if len(instructions) > 300 else ''}")
        
        if len(instructions) == 0:
            print("   ⚠️  No instructions generated!")
            
    except Exception as e:
        print(f"   ❌ Error generating instructions: {e}")
        import traceback
        print(f"   🔧 Full error: {traceback.format_exc()}")
    
    print("\n" + "=" * 60)
    print("🏁 Debug analysis complete!")
    
    # Summary recommendations
    print("\n💡 Recommendations:")
    if 'requirements' in locals() and len(requirements) == 0:
        print("   - Try adding explicit requirement language to your document")
        print("   - Use phrases like 'must', 'shall', 'required', 'prohibited'") 
        print("   - Structure document with numbered sections (1.1, 1.2, etc.)")
        print("   - Include clear legal formatting")
    elif 'requirements' in locals() and len(requirements) > 0:
        print(f"   - Document looks good! Found {len(requirements)} requirements")
        print("   - Requirements should work with the fallback processing")
    else:
        print("   - Check document format and content")
        print("   - Ensure file is a valid .docx document")

def main():
    if len(sys.argv) != 2:
        print("Usage: python debug_fallback.py path/to/your/fallback.docx")
        print("\nExample:")
        print("python debug_fallback.py my_contract_template.docx")
        sys.exit(1)
    
    doc_path = sys.argv[1]
    debug_fallback_document(doc_path)

if __name__ == "__main__":
    main()