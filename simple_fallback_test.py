#!/usr/bin/env python3
"""
Simple fallback document tester - standalone script with minimal dependencies
Usage: python simple_fallback_test.py path/to/your/fallback.docx
"""

import sys
import os
import re
from pathlib import Path

try:
    from docx import Document
except ImportError:
    print("❌ python-docx not installed. Run: pip install python-docx")
    sys.exit(1)

def extract_text_simple(doc_path: str) -> str:
    """Simple text extraction from docx"""
    try:
        doc = Document(doc_path)
        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text.strip())
        return "\n".join(text_parts)
    except Exception as e:
        return f"Error: {e}"

def find_requirements_simple(text: str) -> list:
    """Simple requirement detection"""
    requirements = []
    
    # Common requirement words
    requirement_patterns = [
        r'\b(must|shall|required|mandatory)\b.*?[.!?]',
        r'\b(prohibited|forbidden|not permitted|not allowed)\b.*?[.!?]',
        r'\b(will|should)\b.*?[.!?]'
    ]
    
    lines = text.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        for pattern in requirement_patterns:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                requirement_text = match.group(0)
                
                # Determine type
                req_type = "unknown"
                lower_text = requirement_text.lower()
                if any(word in lower_text for word in ['must', 'shall', 'required', 'mandatory']):
                    req_type = "mandatory"
                elif any(word in lower_text for word in ['prohibited', 'forbidden', 'not permitted']):
                    req_type = "prohibited"
                elif any(word in lower_text for word in ['will', 'should']):
                    req_type = "recommended"
                
                requirements.append({
                    'text': requirement_text,
                    'type': req_type,
                    'line': line_num,
                    'full_line': line
                })
    
    return requirements

def analyze_document_structure(text: str) -> dict:
    """Analyze basic document structure"""
    lines = text.split('\n')
    
    # Look for numbered sections
    section_pattern = r'^\s*(\d+\.?\d*\.?\d*)\s+'
    sections = []
    
    for line in lines:
        if re.match(section_pattern, line.strip()):
            sections.append(line.strip())
    
    # Look for title-like lines (short, all caps, or title case)
    titles = []
    for line in lines:
        line = line.strip()
        if line and (line.isupper() or (len(line.split()) <= 6 and line.istitle())):
            titles.append(line)
    
    return {
        'total_lines': len([l for l in lines if l.strip()]),
        'sections': sections[:10],  # First 10 sections
        'section_count': len(sections),
        'potential_titles': titles[:5],  # First 5 titles
        'has_numbering': len(sections) > 0
    }

def simple_fallback_test(doc_path: str):
    """Simple test of fallback document"""
    
    if not os.path.exists(doc_path):
        print(f"❌ File not found: {doc_path}")
        return
    
    if not doc_path.lower().endswith('.docx'):
        print("❌ File must be a .docx file")
        return
    
    print(f"🔍 Simple Fallback Document Analysis")
    print(f"📄 File: {doc_path}")
    print("=" * 60)
    
    # Extract text
    print("\n1️⃣ Extracting text...")
    text = extract_text_simple(doc_path)
    
    if text.startswith("Error:"):
        print(f"   ❌ {text}")
        return
    
    print(f"   ✅ Extracted {len(text)} characters")
    print(f"   📄 Text preview: {text[:200]}{'...' if len(text) > 200 else ''}")
    
    if len(text.strip()) == 0:
        print("   ⚠️  Document appears to be empty!")
        return
    
    # Analyze structure
    print("\n2️⃣ Analyzing document structure...")
    structure = analyze_document_structure(text)
    
    print(f"   📊 Total text lines: {structure['total_lines']}")
    print(f"   📊 Numbered sections found: {structure['section_count']}")
    print(f"   📊 Has hierarchical numbering: {'Yes' if structure['has_numbering'] else 'No'}")
    
    if structure['sections']:
        print("   📋 Sample sections:")
        for section in structure['sections'][:5]:
            print(f"      {section}")
        if len(structure['sections']) > 5:
            print(f"      ... and {len(structure['sections']) - 5} more")
    
    if structure['potential_titles']:
        print("   📋 Potential titles/headers:")
        for title in structure['potential_titles']:
            print(f"      {title}")
    
    # Find requirements
    print("\n3️⃣ Looking for requirements...")
    requirements = find_requirements_simple(text)
    
    print(f"   ✅ Found {len(requirements)} potential requirements")
    
    if requirements:
        # Group by type
        by_type = {}
        for req in requirements:
            req_type = req['type']
            if req_type not in by_type:
                by_type[req_type] = []
            by_type[req_type].append(req)
        
        print("   📊 Requirements by type:")
        for req_type, reqs in by_type.items():
            print(f"      {req_type}: {len(reqs)} requirements")
        
        print("\n   📝 Sample requirements:")
        for i, req in enumerate(requirements[:5]):
            print(f"      {i+1}. [{req['type'].upper()}] {req['text']}")
            print(f"         (Line {req['line']})")
        
        if len(requirements) > 5:
            print(f"      ... and {len(requirements) - 5} more requirements")
    
    else:
        print("   ⚠️  No requirements found!")
        print("\n   💡 Common requirement words to look for:")
        print("      - must, shall, required, mandatory")
        print("      - prohibited, forbidden, not permitted")
        print("      - will, should")
        print("\n   💡 Your document might need:")
        print("      - More explicit requirement language")
        print("      - Numbered sections (1.1, 1.2, etc.)")
        print("      - Formal contract/legal structure")
    
    print("\n" + "=" * 60)
    print("🏁 Simple analysis complete!")
    
    # Summary and recommendations
    print("\n💡 Summary:")
    if len(requirements) > 0:
        print(f"   ✅ Document looks promising! Found {len(requirements)} requirements")
        print("   ✅ Should work with the fallback processing system")
    else:
        print("   ⚠️  No requirements detected - fallback processing may not work")
        print("   💡 Try adding explicit requirement language to your document")
    
    if not structure['has_numbering']:
        print("   💡 Consider adding numbered sections (1.1, 1.2, etc.) for better parsing")
    
    return len(requirements) > 0

def main():
    if len(sys.argv) != 2:
        print("Usage: python simple_fallback_test.py path/to/your/fallback.docx")
        print("\nExample:")
        print("python simple_fallback_test.py my_contract_template.docx")
        print("\nThis script provides a simple analysis of your fallback document")
        print("to help debug why the system might not be finding requirements.")
        sys.exit(1)
    
    doc_path = sys.argv[1]
    success = simple_fallback_test(doc_path)
    
    if success:
        print(f"\n🎉 Document analysis suggests it should work with the fallback system!")
    else:
        print(f"\n🔧 Document may need modification to work with the fallback system.")

if __name__ == "__main__":
    main()