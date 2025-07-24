#!/usr/bin/env python3
"""
Debug the full document parsing pipeline step by step
"""

import sys
import os

backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

def debug_full_parsing():
    """Debug each step of the full parsing pipeline"""
    
    doc_path = "sample_fallback_contract.docx"
    if not os.path.exists(doc_path):
        print(f"❌ Sample document {doc_path} not found")
        return
    
    try:
        from legal_document_processor import LegalDocumentParser
        
        # Get the parser
        parser = LegalDocumentParser()
        
        print("🔍 Debugging full document parsing pipeline...")
        print(f"📄 Document: {doc_path}")
        
        # Step 1: Text extraction
        print("\n1️⃣ Text extraction...")
        try:
            # Try the same method the parser uses
            from main import extract_text_for_llm
            text_content = extract_text_for_llm(doc_path) or ""
            print(f"   ✅ Extracted {len(text_content)} characters")
            print(f"   📄 First 200 chars: {text_content[:200]}...")
        except ImportError:
            print("   ⚠️  Could not import extract_text_for_llm from main")
            # Try fallback
            from docx import Document
            doc = Document(doc_path)
            text_content = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            print(f"   ✅ Fallback extraction: {len(text_content)} characters")
        
        if not text_content:
            print("   ❌ No text extracted - cannot continue")
            return
        
        # Step 2: Title extraction
        print("\n2️⃣ Title extraction...")
        title = parser._extract_title(text_content)
        print(f"   📋 Title: '{title}'")
        
        # Step 3: Section parsing  
        print("\n3️⃣ Section parsing...")
        sections = parser._parse_hierarchical_sections(text_content)
        print(f"   📊 Sections found: {len(sections)}")
        
        for i, section in enumerate(sections):
            print(f"   Section {i+1}: {section.number} - {section.title}")
            print(f"      Content length: {len(section.content)}")
            print(f"      Requirements: {len(section.requirements)}")
        
        # Step 4: All requirements extraction
        print("\n4️⃣ All requirements extraction...")
        all_requirements = parser._extract_all_requirements(text_content, sections)
        print(f"   📊 Total requirements: {len(all_requirements)}")
        
        for i, req in enumerate(all_requirements[:5]):
            print(f"   Req {i+1}: [{req.requirement_type}] {req.text[:60]}{'...' if len(req.text) > 60 else ''}")
        
        # Step 5: Try the full parse_legal_document function
        print("\n5️⃣ Full parse_legal_document...")
        from legal_document_processor import parse_legal_document
        structure = parse_legal_document(doc_path)
        
        print(f"   📊 Final result:")
        print(f"      Title: {structure.title}")
        print(f"      Sections: {len(structure.sections)}")
        print(f"      Requirements: {len(structure.requirements)}")
        
        # Check if there's a mismatch
        if len(sections) != len(structure.sections):
            print(f"   🚨 MISMATCH: Direct parsing found {len(sections)} sections, full parsing found {len(structure.sections)}")
        
        if len(all_requirements) != len(structure.requirements):
            print(f"   🚨 MISMATCH: Direct extraction found {len(all_requirements)} requirements, full parsing found {len(structure.requirements)}")
        
    except Exception as e:
        print(f"❌ Error in debugging: {e}")
        import traceback
        print(traceback.format_exc())

def main():
    print("🔧 Debugging Full Document Parsing Pipeline")
    print("=" * 55)
    
    debug_full_parsing()

if __name__ == "__main__":
    main()