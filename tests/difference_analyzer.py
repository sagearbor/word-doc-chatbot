"""
LLM-Powered Document Difference Analyzer

This module provides advanced document comparison capabilities using LLM analysis
to understand the differences between input, fallback, and expected documents.
It generates markdown-formatted analysis reports for test-driven development.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json

# Import existing backend components
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from word_processor import extract_text_for_llm, extract_tracked_changes_as_text, get_document_xml_raw_text
    from llm_handler import get_llm_analysis_from_summary, get_llm_analysis_from_raw_xml
    from ai_client import get_ai_client
except ImportError:
    print("Warning: Could not import backend modules. Analysis will be limited.")

@dataclass
class DocumentAnalysis:
    """Results of document analysis"""
    document_type: str
    content_summary: str
    tracked_changes: List[str]
    requirements: List[str]
    structure_info: Dict[str, any]
    word_count: int
    complexity_score: float

@dataclass
class DifferenceReport:
    """Comprehensive difference analysis between documents"""
    test_case_id: str
    input_analysis: DocumentAnalysis
    fallback_analysis: DocumentAnalysis  
    expected_analysis: DocumentAnalysis
    required_changes: List[str]
    fallback_requirements: List[str]
    change_instructions: str
    confidence_score: float
    markdown_report: str

class DocumentDifferenceAnalyzer:
    """Advanced document comparison using LLM analysis"""
    
    def __init__(self):
        """Initialize the difference analyzer"""
        self.ai_client = None
        try:
            self.ai_client = get_ai_client()
            print("LLM client initialized for document analysis")
        except Exception as e:
            print(f"Warning: Could not initialize LLM client: {e}")
    
    def analyze_document(self, doc_path: str, doc_type: str = "unknown") -> DocumentAnalysis:
        """Analyze a single document and extract key information
        
        Args:
            doc_path: Path to document file
            doc_type: Type of document (input, fallback, expected)
            
        Returns:
            DocumentAnalysis with extracted information
        """
        try:
            print(f"Analyzing {doc_type} document: {Path(doc_path).name}")
            
            # Extract text content
            try:
                content = extract_text_for_llm(doc_path)
                word_count = len(content.split()) if content else 0
            except Exception as e:
                print(f"Could not extract text content: {e}")
                content = ""
                word_count = 0
            
            # Extract tracked changes
            tracked_changes = []
            try:
                changes_text = extract_tracked_changes_as_text(doc_path)
                if changes_text:
                    # Parse tracked changes into list
                    changes_lines = changes_text.split('\n')
                    tracked_changes = [line.strip() for line in changes_lines if line.strip()]
            except Exception as e:
                print(f"Could not extract tracked changes: {e}")
            
            # Analyze requirements (for fallback documents)
            requirements = []
            if doc_type == "fallback":
                requirements = self._extract_requirements_from_text(content)
            
            # Generate content summary
            content_summary = self._generate_content_summary(content, doc_type)
            
            # Calculate complexity score
            complexity_score = self._calculate_complexity_score(content, tracked_changes)
            
            # Structure analysis
            structure_info = self._analyze_document_structure(content)
            
            return DocumentAnalysis(
                document_type=doc_type,
                content_summary=content_summary,
                tracked_changes=tracked_changes,
                requirements=requirements,
                structure_info=structure_info,
                word_count=word_count,
                complexity_score=complexity_score
            )
            
        except Exception as e:
            print(f"Error analyzing document {doc_path}: {e}")
            return DocumentAnalysis(
                document_type=doc_type,
                content_summary=f"Error analyzing document: {e}",
                tracked_changes=[],
                requirements=[],
                structure_info={},
                word_count=0,
                complexity_score=0.0
            )
    
    def generate_difference_analysis(self, input_doc: str, fallback_doc: str, 
                                   expected_doc: str, test_case_id: str = "unknown") -> DifferenceReport:
        """Generate comprehensive difference analysis between three documents
        
        Args:
            input_doc: Path to input document with tracked changes
            fallback_doc: Path to fallback requirements document
            expected_doc: Path to expected output document  
            test_case_id: Identifier for this test case
            
        Returns:
            DifferenceReport with comprehensive analysis
        """
        try:
            print(f"Generating difference analysis for test case: {test_case_id}")
            
            # Analyze each document
            input_analysis = self.analyze_document(input_doc, "input")
            fallback_analysis = self.analyze_document(fallback_doc, "fallback")
            expected_analysis = self.analyze_document(expected_doc, "expected")
            
            # Generate LLM-powered analysis
            required_changes = self._identify_required_changes(input_analysis, expected_analysis)
            fallback_requirements = fallback_analysis.requirements
            change_instructions = self._generate_change_instructions(
                input_analysis, fallback_analysis, expected_analysis
            )
            
            # Calculate confidence score
            confidence_score = self._calculate_analysis_confidence(
                input_analysis, fallback_analysis, expected_analysis
            )
            
            # Generate markdown report
            markdown_report = self._generate_markdown_report(
                test_case_id, input_analysis, fallback_analysis, expected_analysis,
                required_changes, fallback_requirements, change_instructions, confidence_score
            )
            
            return DifferenceReport(
                test_case_id=test_case_id,
                input_analysis=input_analysis,
                fallback_analysis=fallback_analysis,
                expected_analysis=expected_analysis,
                required_changes=required_changes,
                fallback_requirements=fallback_requirements,
                change_instructions=change_instructions,
                confidence_score=confidence_score,
                markdown_report=markdown_report
            )
            
        except Exception as e:
            print(f"Error generating difference analysis: {e}")
            # Return minimal error report
            error_report = f"# Error Analysis Report\n\nFailed to analyze documents: {e}"
            return DifferenceReport(
                test_case_id=test_case_id,
                input_analysis=DocumentAnalysis("error", str(e), [], [], {}, 0, 0.0),
                fallback_analysis=DocumentAnalysis("error", str(e), [], [], {}, 0, 0.0),
                expected_analysis=DocumentAnalysis("error", str(e), [], [], {}, 0, 0.0),
                required_changes=[],
                fallback_requirements=[],
                change_instructions="",
                confidence_score=0.0,
                markdown_report=error_report
            )
    
    def _extract_requirements_from_text(self, content: str) -> List[str]:
        """Extract requirements from document content"""
        requirements = []
        
        if not content:
            return requirements
        
        # Look for requirement patterns
        requirement_patterns = [
            r'\bmust\b.*?[.!]',
            r'\bshall\b.*?[.!]', 
            r'\brequired\b.*?[.!]',
            r'\bmandatory\b.*?[.!]',
            r'\bobligat\w+\b.*?[.!]'
        ]
        
        import re
        for pattern in requirement_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                cleaned = match.strip().replace('\n', ' ').replace('  ', ' ')
                if len(cleaned) > 10:  # Filter out very short matches
                    requirements.append(cleaned)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_requirements = []
        for req in requirements:
            if req.lower() not in seen:
                seen.add(req.lower())
                unique_requirements.append(req)
        
        return unique_requirements[:20]  # Limit to top 20 requirements
    
    def _generate_content_summary(self, content: str, doc_type: str) -> str:
        """Generate a brief summary of document content"""
        if not content:
            return f"No content available for {doc_type} document"
        
        # Simple summary based on content length and key terms
        word_count = len(content.split())
        
        # Count key legal terms
        legal_terms = ['shall', 'must', 'agreement', 'contract', 'party', 'obligation']
        term_counts = {term: content.lower().count(term) for term in legal_terms}
        
        # Identify document characteristics
        characteristics = []
        if term_counts['agreement'] > 0 or term_counts['contract'] > 0:
            characteristics.append("legal agreement")
        if term_counts['shall'] > 10:
            characteristics.append("formal obligations")
        if term_counts['must'] > 5:
            characteristics.append("mandatory requirements")
        
        summary = f"{doc_type.title()} document ({word_count} words)"
        if characteristics:
            summary += f" containing {', '.join(characteristics)}"
        
        return summary
    
    def _calculate_complexity_score(self, content: str, tracked_changes: List[str]) -> float:
        """Calculate document complexity score (0.0 to 1.0)"""
        if not content:
            return 0.0
        
        factors = []
        
        # Word count factor
        word_count = len(content.split())
        if word_count > 1000:
            factors.append(0.3)
        elif word_count > 500:
            factors.append(0.2)
        else:
            factors.append(0.1)
        
        # Legal complexity factor
        legal_terms = ['whereas', 'therefore', 'notwithstanding', 'pursuant', 'herein']
        legal_count = sum(content.lower().count(term) for term in legal_terms)
        if legal_count > 10:
            factors.append(0.3)
        elif legal_count > 5:
            factors.append(0.2)
        else:
            factors.append(0.1)
        
        # Tracked changes factor
        if len(tracked_changes) > 10:
            factors.append(0.3)
        elif len(tracked_changes) > 5:
            factors.append(0.2)
        else:
            factors.append(0.1)
        
        # Structure factor (sentences and paragraphs)
        sentence_count = content.count('.') + content.count('!') + content.count('?')
        if sentence_count > 100:
            factors.append(0.1)
        
        return min(sum(factors), 1.0)
    
    def _analyze_document_structure(self, content: str) -> Dict[str, any]:
        """Analyze document structure and organization"""
        if not content:
            return {}
        
        structure = {
            'word_count': len(content.split()),
            'character_count': len(content),
            'paragraph_count': len([p for p in content.split('\n') if p.strip()]),
            'sentence_count': content.count('.') + content.count('!') + content.count('?'),
        }
        
        # Look for structural elements
        structure['has_numbering'] = bool(re.search(r'\d+\.\d+', content))
        structure['has_whereas_clauses'] = 'WHEREAS' in content.upper()
        structure['has_signature_blocks'] = 'signature' in content.lower()
        structure['has_definitions'] = 'means' in content.lower() and 'definition' in content.lower()
        
        return structure
    
    def _identify_required_changes(self, input_analysis: DocumentAnalysis, 
                                 expected_analysis: DocumentAnalysis) -> List[str]:
        """Identify what changes are required to transform input to expected output"""
        changes = []
        
        # Compare tracked changes
        input_changes = set(input_analysis.tracked_changes)
        expected_changes = set(expected_analysis.tracked_changes)
        
        new_changes = expected_changes - input_changes
        removed_changes = input_changes - expected_changes
        
        for change in new_changes:
            changes.append(f"ADD: {change}")
        
        for change in removed_changes:
            changes.append(f"REMOVE: {change}")
        
        # Compare word counts
        word_diff = expected_analysis.word_count - input_analysis.word_count
        if abs(word_diff) > 50:
            changes.append(f"CONTENT: {word_diff:+d} words difference")
        
        return changes
    
    def _generate_change_instructions(self, input_analysis: DocumentAnalysis,
                                    fallback_analysis: DocumentAnalysis,
                                    expected_analysis: DocumentAnalysis) -> str:
        """Generate clear instructions for making required changes"""
        
        instructions = []
        
        # Instructions based on fallback requirements
        if fallback_analysis.requirements:
            instructions.append("Apply the following requirements from the fallback document:")
            for i, req in enumerate(fallback_analysis.requirements[:10], 1):
                instructions.append(f"{i}. {req}")
        
        # Instructions based on structural differences
        if expected_analysis.word_count > input_analysis.word_count:
            instructions.append(f"\nExpand content by approximately {expected_analysis.word_count - input_analysis.word_count} words")
        
        # Instructions based on tracked changes
        expected_changes = len(expected_analysis.tracked_changes)
        input_changes = len(input_analysis.tracked_changes)
        if expected_changes > input_changes:
            instructions.append(f"\nAdd {expected_changes - input_changes} additional tracked changes")
        
        return '\n'.join(instructions) if instructions else "No specific instructions generated"
    
    def _calculate_analysis_confidence(self, input_analysis: DocumentAnalysis,
                                     fallback_analysis: DocumentAnalysis, 
                                     expected_analysis: DocumentAnalysis) -> float:
        """Calculate confidence score for the analysis (0.0 to 1.0)"""
        
        confidence_factors = []
        
        # Content availability factor
        if input_analysis.word_count > 100:
            confidence_factors.append(0.3)
        if fallback_analysis.word_count > 100:
            confidence_factors.append(0.3)
        if expected_analysis.word_count > 100:
            confidence_factors.append(0.3)
        
        # Requirements extraction factor
        if len(fallback_analysis.requirements) > 0:
            confidence_factors.append(0.1)
        
        return min(sum(confidence_factors), 1.0)
    
    def _generate_markdown_report(self, test_case_id: str, input_analysis: DocumentAnalysis,
                                fallback_analysis: DocumentAnalysis, expected_analysis: DocumentAnalysis,
                                required_changes: List[str], fallback_requirements: List[str],
                                change_instructions: str, confidence_score: float) -> str:
        """Generate comprehensive markdown analysis report"""
        
        report = f"""# Document Difference Analysis Report

## Test Case: {test_case_id}
**Analysis Confidence:** {confidence_score:.1%}
**Generated:** {datetime.now().isoformat()}

---

## Document Overview

### Input Document Analysis
- **Type:** {input_analysis.document_type}
- **Summary:** {input_analysis.content_summary}
- **Word Count:** {input_analysis.word_count:,}
- **Complexity Score:** {input_analysis.complexity_score:.2f}
- **Tracked Changes:** {len(input_analysis.tracked_changes)}

### Fallback Document Analysis  
- **Type:** {fallback_analysis.document_type}
- **Summary:** {fallback_analysis.content_summary}
- **Word Count:** {fallback_analysis.word_count:,}
- **Complexity Score:** {fallback_analysis.complexity_score:.2f}
- **Requirements Extracted:** {len(fallback_analysis.requirements)}

### Expected Output Analysis
- **Type:** {expected_analysis.document_type}  
- **Summary:** {expected_analysis.content_summary}
- **Word Count:** {expected_analysis.word_count:,}
- **Complexity Score:** {expected_analysis.complexity_score:.2f}
- **Tracked Changes:** {len(expected_analysis.tracked_changes)}

---

## Required Changes Analysis

The following changes must be made to transform the input document into the expected output:

"""
        
        if required_changes:
            for change in required_changes:
                report += f"- {change}\n"
        else:
            report += "- No specific changes identified\n"
        
        report += f"""
---

## Fallback Requirements

The fallback document contains the following key requirements:

"""
        
        if fallback_requirements:
            for i, req in enumerate(fallback_requirements[:10], 1):
                report += f"{i}. {req}\n"
        else:
            report += "No requirements extracted from fallback document.\n"
        
        report += f"""
---

## Generated Change Instructions

{change_instructions}

---

## Document Structure Comparison

| Metric | Input | Fallback | Expected |
|--------|--------|----------|----------|
| Word Count | {input_analysis.word_count:,} | {fallback_analysis.word_count:,} | {expected_analysis.word_count:,} |
| Tracked Changes | {len(input_analysis.tracked_changes)} | {len(fallback_analysis.tracked_changes)} | {len(expected_analysis.tracked_changes)} |
| Complexity | {input_analysis.complexity_score:.2f} | {fallback_analysis.complexity_score:.2f} | {expected_analysis.complexity_score:.2f} |

---

## Analysis Insights

### Key Observations
- **Content Growth:** {expected_analysis.word_count - input_analysis.word_count:+,} words from input to expected
- **Change Volume:** {len(expected_analysis.tracked_changes) - len(input_analysis.tracked_changes):+d} tracked changes difference
- **Requirement Coverage:** {len(fallback_requirements)} requirements identified for application

### Recommendations for LLM Processing
1. Focus on applying the {len(fallback_requirements)} extracted requirements
2. Ensure tracked changes are properly added for all modifications
3. Maintain legal document structure and formatting
4. Validate that all requirements are addressed in the final output

---

*Report generated by Document Difference Analyzer v1.0*
"""
        
        return report

# Add datetime import at the top
from datetime import datetime

# Convenience function for standalone usage
def analyze_document_differences(input_doc: str, fallback_doc: str, expected_doc: str, 
                               test_case_id: str = "standalone_analysis") -> str:
    """
    Standalone function to analyze differences between three documents
    
    Args:
        input_doc: Path to input document
        fallback_doc: Path to fallback document  
        expected_doc: Path to expected document
        test_case_id: Identifier for the analysis
        
    Returns:
        Markdown formatted difference analysis report
    """
    analyzer = DocumentDifferenceAnalyzer()
    report = analyzer.generate_difference_analysis(input_doc, fallback_doc, expected_doc, test_case_id)
    return report.markdown_report

if __name__ == "__main__":
    # Example usage for testing
    print("Document Difference Analyzer - Test Mode")
    print("This module provides LLM-powered document comparison capabilities.")
    print("Import this module and use analyze_document_differences() function.")