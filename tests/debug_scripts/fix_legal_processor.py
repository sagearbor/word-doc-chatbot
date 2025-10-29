#!/usr/bin/env python3
"""
Fix the legal document processor to handle simple numbered sections
"""

import sys
import os
import re

backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

def analyze_document_structure():
    """Analyze what our sample document structure looks like"""
    
    sample_text = """SAMPLE CONTRACT REQUIREMENTS
1. GENERAL REQUIREMENTS
1.1 The Contractor must provide all services in accordance with professional standards.
1.2 All deliverables shall be submitted within the agreed timeline.
1.3 The Contractor is required to maintain confidentiality of all project information.
2. QUALITY STANDARDS
2.1 All work must meet industry best practices and standards.
2.2 The Contractor shall provide regular progress reports.
2.3 Any defects must be corrected within 5 business days.
3. COMPLIANCE REQUIREMENTS
3.1 The Contractor must comply with all applicable laws and regulations.
3.2 Safety protocols are required to be followed at all times.
3.3 Documentation shall be maintained for audit purposes.
4. PROHIBITED ACTIVITIES
4.1 Subcontracting is prohibited without written approval.
4.2 The Contractor must not disclose confidential information.
4.3 Use of project resources for personal purposes is not permitted."""

    print("🔍 Analyzing document structure...")
    lines = sample_text.split('\n')
    
    current_patterns = [
        r'^\s*(\d+\.\d+(?:\.\d+)*)\s+(.+)$',  # 1.1, 1.2.3 format
        r'^\s*(\d+)\.\s+(.+)$',               # 1. format
        r'^\s*\(([a-z])\)\s+(.+)$',          # (a) format
        r'^\s*\((\d+)\)\s+(.+)$',            # (1) format
    ]
    
    print("\n📋 Testing current patterns against document lines:")
    for line_num, line in enumerate(lines, 1):
        if not line.strip():
            continue
            
        matches_pattern = False
        for i, pattern in enumerate(current_patterns):
            match = re.match(pattern, line.strip())
            if match:
                print(f"   ✅ Line {line_num}: Pattern {i+1} matched '{line.strip()}'")
                print(f"       Groups: {match.groups()}")
                matches_pattern = True
                break
        
        if not matches_pattern:
            print(f"   ❌ Line {line_num}: NO PATTERN MATCHED '{line.strip()}'")
    
    # Test improved patterns
    print("\n🔧 Testing improved patterns:")
    improved_patterns = [
        r'^\s*(\d+\.\d+(?:\.\d+)*)\s+(.+)$',  # 1.1, 1.2.3 format  
        r'^\s*(\d+)\.\s+(.+)$',               # 1. format
        r'^\s*(\d+)\s+(.+)$',                 # Simple "1 TITLE" format (NEW)
        r'^\s*\(([a-z])\)\s+(.+)$',          # (a) format
        r'^\s*\((\d+)\)\s+(.+)$',            # (1) format
    ]
    
    for line_num, line in enumerate(lines, 1):
        if not line.strip():
            continue
            
        matches_pattern = False
        for i, pattern in enumerate(improved_patterns):
            match = re.match(pattern, line.strip())
            if match:
                print(f"   ✅ Line {line_num}: Improved Pattern {i+1} matched '{line.strip()}'")
                print(f"       Groups: {match.groups()}")
                matches_pattern = True
                break
        
        if not matches_pattern:
            print(f"   ❌ Line {line_num}: STILL NO MATCH '{line.strip()}'")

def test_requirement_patterns():
    """Test requirement detection patterns"""
    
    sample_requirements = [
        "1.1 The Contractor must provide all services in accordance with professional standards.",
        "1.2 All deliverables shall be submitted within the agreed timeline.",
        "1.3 The Contractor is required to maintain confidentiality of all project information.",
        "2.1 All work must meet industry best practices and standards.",
        "4.1 Subcontracting is prohibited without written approval.",
        "4.2 The Contractor must not disclose confidential information.",
        "4.3 Use of project resources for personal purposes is not permitted."
    ]
    
    # Current requirement patterns
    current_patterns = {
        'mandatory': [
            r'\bmust\s+[\w\s,]+[.!]',
            r'\bshall\s+[\w\s,]+[.!]',
            r'\brequired\s+to[\w\s,]+[.!]',
            r'\bmandatory\s+[\w\s,]+[.!]',
        ],
        'prohibited': [
            r'\bshall\s+not[\w\s,]+[.!]',
            r'\bmust\s+not[\w\s,]+[.!]',
            r'\bprohibited\s+from[\w\s,]+[.!]',
            r'\bmay\s+not[\w\s,]+[.!]',
        ]
    }
    
    print("\n🔍 Testing requirement patterns...")
    
    for req_text in sample_requirements:
        print(f"\n   📝 Testing: {req_text}")
        found_match = False
        
        for req_type, patterns in current_patterns.items():
            for pattern in patterns:
                if re.search(pattern, req_text, re.IGNORECASE):
                    print(f"      ✅ Matched {req_type}: {pattern}")
                    found_match = True
        
        if not found_match:
            print(f"      ❌ NO PATTERN MATCHED")
            
            # Try simpler patterns
            simple_patterns = [
                r'\bmust\b',
                r'\bshall\b', 
                r'\brequired\b',
                r'\bprohibited\b',
                r'\bnot permitted\b'
            ]
            
            for pattern in simple_patterns:
                if re.search(pattern, req_text, re.IGNORECASE):
                    print(f"      💡 Simple pattern would work: {pattern}")

def main():
    print("🔧 Legal Document Processor Analysis & Fix")
    print("=" * 50)
    
    analyze_document_structure()
    test_requirement_patterns()
    
    print("\n" + "=" * 50)
    print("💡 Recommendations:")
    print("1. Add pattern for simple numbered sections: r'^\\s*(\\d+)\\s+(.+)$'")
    print("2. Simplify requirement patterns to be more flexible")
    print("3. The current patterns are too restrictive for common document formats")

if __name__ == "__main__":
    main()