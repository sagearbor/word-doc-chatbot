#!/usr/bin/env python3
"""
Test the fixed legal processor directly
"""

import sys
import os

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

def test_fixed_patterns():
    """Test the fixed requirement patterns"""
    
    test_requirements = [
        "1.1 The Contractor must provide all services in accordance with professional standards.",
        "1.2 All deliverables shall be submitted within the agreed timeline.", 
        "1.3 The Contractor is required to maintain confidentiality of all project information.",
        "2.1 All work must meet industry best practices and standards.",
        "4.1 Subcontracting is prohibited without written approval.",
        "4.2 The Contractor must not disclose confidential information.",
        "4.3 Use of project resources for personal purposes is not permitted."
    ]
    
    # Import the fixed patterns
    try:
        from legal_document_processor import LegalDocumentParser
        parser = LegalDocumentParser()
        
        print("🔍 Testing fixed requirement patterns...")
        
        total_found = 0
        for req_text in test_requirements:
            print(f"\n   📝 Testing: {req_text}")
            
            # Test the _extract_requirements_from_text method
            requirements = parser._extract_requirements_from_text(req_text, "test")
            
            if requirements:
                for req in requirements:
                    print(f"      ✅ Found {req.requirement_type}: {req.text}")
                    total_found += 1
            else:
                print(f"      ❌ No requirements found")
        
        print(f"\n📊 Total requirements found: {total_found} out of {len(test_requirements)}")
        return total_found > 0
        
    except Exception as e:
        print(f"❌ Error testing patterns: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_section_parsing():
    """Test section parsing"""
    
    sample_text = """SAMPLE CONTRACT REQUIREMENTS
1. GENERAL REQUIREMENTS
1.1 The Contractor must provide all services in accordance with professional standards.
1.2 All deliverables shall be submitted within the agreed timeline.
1.3 The Contractor is required to maintain confidentiality of all project information.
2. QUALITY STANDARDS
2.1 All work must meet industry best practices and standards.
2.2 The Contractor shall provide regular progress reports.
2.3 Any defects must be corrected within 5 business days."""

    try:
        from legal_document_processor import LegalDocumentParser
        parser = LegalDocumentParser()
        
        print("🔍 Testing section parsing...")
        
        sections = parser._parse_hierarchical_sections(sample_text)
        
        print(f"📊 Found {len(sections)} sections")
        
        for i, section in enumerate(sections):
            print(f"   Section {i+1}: {section.number} - {section.title}")
            print(f"      Content: {section.content[:100]}{'...' if len(section.content) > 100 else ''}")
            print(f"      Requirements: {len(section.requirements)}")
            
            for req in section.requirements[:2]:  # Show first 2 requirements
                print(f"         - [{req.requirement_type}] {req.text[:60]}{'...' if len(req.text) > 60 else ''}")
        
        return len(sections) > 0
        
    except Exception as e:
        print(f"❌ Error testing section parsing: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def test_full_document_parsing(doc_path):
    """Test full document parsing"""
    
    try:
        from legal_document_processor import parse_legal_document
        
        print(f"🔍 Testing full document parsing: {doc_path}")
        
        structure = parse_legal_document(doc_path)
        
        print(f"📊 Results:")
        print(f"   Title: {structure.title}")
        print(f"   Sections: {len(structure.sections)}")
        print(f"   Requirements: {len(structure.requirements)}")
        print(f"   Authors: {structure.authors}")
        
        if structure.requirements:
            print(f"\n📋 Requirements found:")
            for i, req in enumerate(structure.requirements[:5]):  # Show first 5
                print(f"   {i+1}. [{req.requirement_type.upper()}] {req.text}")
                print(f"      Section: {req.section}, Priority: {req.priority}")
        
        return len(structure.requirements) > 0
        
    except Exception as e:
        print(f"❌ Error testing full parsing: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    print("🔧 Testing Fixed Legal Document Processor")
    print("=" * 50)
    
    # Test 1: Requirement patterns
    patterns_work = test_fixed_patterns()
    
    print("\n" + "=" * 50)
    
    # Test 2: Section parsing
    sections_work = test_section_parsing()
    
    print("\n" + "=" * 50)
    
    # Test 3: Full document (if sample exists)
    sample_path = "sample_fallback_contract.docx"
    if os.path.exists(sample_path):
        full_parsing_works = test_full_document_parsing(sample_path)
    else:
        print(f"⚠️  Sample document {sample_path} not found - skipping full parsing test")
        full_parsing_works = False
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   Requirement patterns: {'✅' if patterns_work else '❌'}")
    print(f"   Section parsing: {'✅' if sections_work else '❌'}")
    print(f"   Full document parsing: {'✅' if full_parsing_works else '❌'}")
    
    if all([patterns_work, sections_work, full_parsing_works]):
        print("\n🎉 All tests passed! The legal processor should now work.")
    else:
        print("\n🔧 Some tests failed. More debugging needed.")

if __name__ == "__main__":
    main()