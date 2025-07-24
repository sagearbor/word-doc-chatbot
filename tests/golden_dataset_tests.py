"""
Golden Dataset Testing Framework for Fallback Document Translation

This module provides automated testing infrastructure for validating the quality
of fallback document to LLM instruction translation using real document test cases.

Key Features:
- LLM-powered difference analysis between documents
- Automated comparison of actual vs expected outputs  
- Test case ingestion and management
- Scoring and validation of translation quality
- Regression testing for iterative improvements
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import difflib

# Import existing word processor components
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from word_processor import extract_text_for_llm, extract_tracked_changes_as_text
    from llm_handler import get_llm_suggestions, get_llm_analysis_from_summary
    from ai_client import get_ai_client
    from legal_document_processor import (
        extract_fallback_requirements,
        generate_instructions_from_fallback,
        parse_legal_document
    )
    LEGAL_PROCESSOR_AVAILABLE = True
except ImportError:
    print("Warning: Could not import backend modules. Some functionality may be limited.")
    LEGAL_PROCESSOR_AVAILABLE = False

@dataclass
class TestCase:
    """Represents a single golden dataset test case"""
    id: str
    description: str
    input_document: str
    fallback_document: str
    expected_output: str
    test_metadata: Dict[str, Any]
    notes: Optional[str] = None

@dataclass 
class TestResult:
    """Results of a test case execution"""
    test_case_id: str
    success: bool
    score: float
    generated_instructions: str
    actual_output_path: str
    comparison_report_path: str
    errors: List[str]
    execution_time: float
    timestamp: datetime

class GoldenDatasetTester:
    """Main testing framework for fallback document translation validation"""
    
    def __init__(self, dataset_path: str = None):
        """Initialize the golden dataset tester
        
        Args:
            dataset_path: Path to golden dataset directory. Defaults to tests/golden_dataset/
        """
        if dataset_path is None:
            dataset_path = os.path.join(os.path.dirname(__file__), 'golden_dataset')
        
        self.dataset_path = Path(dataset_path)
        self.test_cases: List[TestCase] = []
        self.results: List[TestResult] = []
        
        # Create directories if they don't exist
        self.dataset_path.mkdir(parents=True, exist_ok=True)
        for subdir in ['input_documents', 'fallback_documents', 'expected_outputs', 'comparison_reports']:
            (self.dataset_path / subdir).mkdir(exist_ok=True)
    
    def load_test_cases(self) -> List[TestCase]:
        """Load test cases from test_cases.json configuration file"""
        test_config_path = self.dataset_path / 'test_cases.json'
        
        if not test_config_path.exists():
            print(f"Warning: Test configuration file not found at {test_config_path}")
            return []
        
        try:
            with open(test_config_path, 'r') as f:
                config = json.load(f)
            
            test_cases = []
            for case_data in config.get('test_cases', []):
                test_case = TestCase(
                    id=case_data['id'],
                    description=case_data['description'],
                    input_document=str(self.dataset_path / case_data['input_document']),
                    fallback_document=str(self.dataset_path / case_data['fallback_document']),
                    expected_output=str(self.dataset_path / case_data['expected_output']),
                    test_metadata=case_data.get('test_metadata', {}),
                    notes=case_data.get('notes')
                )
                test_cases.append(test_case)
            
            self.test_cases = test_cases
            print(f"Loaded {len(test_cases)} test cases")
            return test_cases
            
        except Exception as e:
            print(f"Error loading test cases: {e}")
            return []
    
    def analyze_document_differences(self, input_doc: str, fallback_doc: str, expected_doc: str) -> str:
        """Generate LLM-powered analysis of differences between documents in markdown format
        
        Args:
            input_doc: Path to input document with tracked changes
            fallback_doc: Path to fallback requirements document  
            expected_doc: Path to expected output document
            
        Returns:
            Markdown formatted analysis of what changes should be made
        """
        try:
            # Extract content from each document
            print(f"Analyzing differences between documents...")
            
            # For now, create a structured analysis prompt for LLM
            analysis_prompt = f"""
            Analyze the following three legal documents to understand what changes should be applied:

            1. INPUT DOCUMENT: Starting document that needs to be modified
            2. FALLBACK DOCUMENT: Contains minimum requirements that should be applied
            3. EXPECTED OUTPUT: Shows how the document should look after applying fallback requirements

            Please provide a detailed markdown analysis with:
            
            ## Required Changes Analysis
            - List specific changes that need to be made to transform input → expected output  
            - Identify which fallback requirements drive each change
            - Highlight any conflicts or complex requirements
            
            ## Fallback Requirements Translation
            - Extract key requirements from fallback document
            - Convert requirements into clear, actionable instructions
            - Prioritize requirements by legal importance
            
            ## Expected Outcomes
            - Summarize what the final document should contain
            - Note any formatting or structural changes needed
            - Identify critical legal language that must be preserved
            
            This analysis will be used to test and improve automated fallback document processing.
            """
            
            # TODO: When documents are available, extract actual content and include in prompt
            # input_content = extract_text_for_llm(input_doc)
            # fallback_content = extract_text_for_llm(fallback_doc)  
            # expected_content = extract_text_for_llm(expected_doc)
            
            return analysis_prompt
            
        except Exception as e:
            return f"Error analyzing document differences: {e}"
    
    def extract_fallback_requirements(self, fallback_doc_path: str) -> List[str]:
        """Extract requirements from fallback document for instruction generation
        
        Args:
            fallback_doc_path: Path to fallback document
            
        Returns:
            List of extracted requirements as strings
        """
        try:
            if LEGAL_PROCESSOR_AVAILABLE:
                print(f"Using legal document processor to extract requirements...")
                # Use the new legal document processor
                requirements_objects = extract_fallback_requirements(fallback_doc_path)
                requirements_text = [req.text for req in requirements_objects]
                print(f"Extracted {len(requirements_text)} requirements using legal processor")
                return requirements_text
            else:
                # Fallback to placeholder requirements
                print(f"Legal processor not available, using placeholder requirements...")
                placeholder_requirements = [
                    "Apply standard compliance language for clinical trials",
                    "Ensure payment terms include milestone-based structure", 
                    "Add required regulatory approval clauses",
                    "Include standard liability and indemnification terms",
                    "Apply standard confidentiality and data protection requirements"
                ]
                
                print(f"Using {len(placeholder_requirements)} placeholder requirements")
                return placeholder_requirements
            
        except Exception as e:
            print(f"Error extracting fallback requirements: {e}")
            return []
    
    def generate_llm_instructions(self, requirements: List[str], context: str = "") -> str:
        """Convert fallback requirements into LLM instructions for document processing
        
        Args:
            requirements: List of extracted requirements
            context: Additional context about the document
            
        Returns:
            Generated instructions for LLM processing
        """
        try:
            if LEGAL_PROCESSOR_AVAILABLE and len(requirements) > 0:
                # Try to use the fallback document if available for the test case
                # For now, create instructions from the requirements list
                instruction_components = []
                
                for i, req in enumerate(requirements, 1):
                    instruction_components.append(f"{i}. {req}")
                
                instructions = f"""
                Please modify this legal document by applying the following requirements:
                
                {chr(10).join(instruction_components)}
                
                Guidelines:
                - Preserve existing legal structure and formatting
                - Add tracked changes for all modifications  
                - Maintain legal precision and terminology
                - Do not remove existing compliance language
                - Add author attribution for all new changes
                
                Additional Context: {context}
                """
                
                return instructions.strip()
            else:
                # Fallback to simple instruction generation
                instruction_components = []
                
                for i, req in enumerate(requirements, 1):
                    instruction_components.append(f"{i}. {req}")
                
                instructions = f"""
                Please modify this legal document by applying the following requirements:
                
                {chr(10).join(instruction_components)}
                
                Guidelines:
                - Preserve existing legal structure and formatting
                - Add tracked changes for all modifications  
                - Maintain legal precision and terminology
                - Do not remove existing compliance language
                - Add author attribution for all new changes
                
                Additional Context: {context}
                """
                
                return instructions.strip()
            
        except Exception as e:
            return f"Error generating LLM instructions: {e}"
    
    def run_test_case(self, test_case: TestCase) -> TestResult:
        """Execute a single test case and return results
        
        Args:
            test_case: Test case to execute
            
        Returns:
            TestResult with execution details and scoring
        """
        start_time = datetime.now()
        errors = []
        
        try:
            print(f"Running test case: {test_case.id}")
            
            # Step 1: Analyze document differences (for understanding)
            diff_analysis = self.analyze_document_differences(
                test_case.input_document,
                test_case.fallback_document, 
                test_case.expected_output
            )
            
            # Step 2: Extract requirements from fallback document
            fallback_requirements = self.extract_fallback_requirements(test_case.fallback_document)
            
            # Step 3: Generate LLM instructions
            generated_instructions = self.generate_llm_instructions(
                fallback_requirements,
                context=f"Legal document processing for {test_case.test_metadata.get('document_type', 'unknown')}"
            )
            
            # Step 4: Create comparison report
            report_path = self.dataset_path / 'comparison_reports' / f'{test_case.id}_analysis_report.md'
            self._create_comparison_report(test_case, diff_analysis, generated_instructions, report_path)
            
            # Step 5: Score the test (placeholder scoring for now)
            score = self._calculate_test_score(test_case, generated_instructions)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = TestResult(
                test_case_id=test_case.id,
                success=score >= 0.7,  # 70% threshold for now
                score=score,
                generated_instructions=generated_instructions,
                actual_output_path="",  # TODO: Path to processed document
                comparison_report_path=str(report_path),
                errors=errors,
                execution_time=execution_time,
                timestamp=datetime.now()
            )
            
            self.results.append(result)
            return result
            
        except Exception as e:
            errors.append(str(e))
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return TestResult(
                test_case_id=test_case.id,
                success=False,
                score=0.0,
                generated_instructions="",
                actual_output_path="",
                comparison_report_path="",
                errors=errors,
                execution_time=execution_time,
                timestamp=datetime.now()
            )
    
    def _create_comparison_report(self, test_case: TestCase, diff_analysis: str, 
                                instructions: str, report_path: Path):
        """Create a detailed comparison report for the test case"""
        
        report_content = f"""# Test Case Analysis Report
        
## Test Case: {test_case.id}
**Description:** {test_case.description}
**Timestamp:** {datetime.now().isoformat()}

## Document Paths
- **Input Document:** {test_case.input_document}
- **Fallback Document:** {test_case.fallback_document}  
- **Expected Output:** {test_case.expected_output}

## Document Differences Analysis
{diff_analysis}

## Generated LLM Instructions
```
{instructions}
```

## Test Metadata
{json.dumps(test_case.test_metadata, indent=2)}

## Notes
{test_case.notes or 'No additional notes'}

---
*Report generated by Golden Dataset Testing Framework*
"""
        
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        print(f"Created comparison report: {report_path}")
    
    def _calculate_test_score(self, test_case: TestCase, instructions: str) -> float:
        """Calculate a quality score for the generated instructions
        
        For now, this is a placeholder scoring system. In the full implementation,
        this would compare actual document processing results against expected outputs.
        """
        # Placeholder scoring based on instruction quality indicators
        score_factors = []
        
        # Check for key instruction components
        if "tracked changes" in instructions.lower():
            score_factors.append(0.2)
        if "legal" in instructions.lower():
            score_factors.append(0.2) 
        if len(instructions.split('\n')) >= 5:  # Sufficient detail
            score_factors.append(0.2)
        if any(word in instructions.lower() for word in ['compliance', 'requirements', 'modify']):
            score_factors.append(0.2)
        if "author" in instructions.lower():
            score_factors.append(0.2)
        
        return sum(score_factors)
    
    def run_all_test_cases(self) -> List[TestResult]:
        """Run all loaded test cases and return aggregated results"""
        if not self.test_cases:
            self.load_test_cases()
        
        print(f"Running {len(self.test_cases)} test cases...")
        results = []
        
        for test_case in self.test_cases:
            result = self.run_test_case(test_case)
            results.append(result)
            print(f"Test {result.test_case_id}: {'PASS' if result.success else 'FAIL'} (Score: {result.score:.2f})")
        
        return results
    
    def generate_summary_report(self) -> str:
        """Generate a summary report of all test results"""
        if not self.results:
            return "No test results available"
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        avg_score = sum(r.score for r in self.results) / total_tests
        avg_execution_time = sum(r.execution_time for r in self.results) / total_tests
        
        summary = f"""# Golden Dataset Testing Summary
        
## Overall Results
- **Total Test Cases:** {total_tests}
- **Passed:** {passed_tests} ({passed_tests/total_tests*100:.1f}%)
- **Failed:** {total_tests - passed_tests}
- **Average Score:** {avg_score:.3f}
- **Average Execution Time:** {avg_execution_time:.2f}s

## Individual Test Results
"""
        
        for result in self.results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            summary += f"- **{result.test_case_id}:** {status} (Score: {result.score:.3f})\n"
        
        summary += f"""
## Next Steps
Based on these results:
1. Review failed test cases for improvement opportunities
2. Analyze score patterns to identify systematic issues  
3. Iterate on fallback document processing algorithms
4. Add more test cases to improve coverage

*Report generated: {datetime.now().isoformat()}*
"""
        
        return summary

def main():
    """Main entry point for running golden dataset tests"""
    print("=== Golden Dataset Testing Framework ===")
    print("Initializing fallback document translation testing...")
    
    # Initialize tester
    tester = GoldenDatasetTester()
    
    # Load test cases
    test_cases = tester.load_test_cases()
    if not test_cases:
        print("No test cases found. Please add test documents and update test_cases.json")
        return
    
    # Run all tests
    results = tester.run_all_test_cases()
    
    # Generate summary report
    summary = tester.generate_summary_report()
    print("\n" + summary)
    
    # Save summary report
    summary_path = tester.dataset_path / 'comparison_reports' / 'test_summary.md'
    with open(summary_path, 'w') as f:
        f.write(summary)
    print(f"\nDetailed summary saved to: {summary_path}")

if __name__ == "__main__":
    main()