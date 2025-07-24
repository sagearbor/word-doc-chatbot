# Golden Dataset Testing Framework

This directory contains the test infrastructure for validating fallback document to LLM instruction translation quality.

## Directory Structure

```
golden_dataset/
├── input_documents/           # Starting documents with tracked changes
├── fallback_documents/        # Fallback requirement documents  
├── expected_outputs/          # How documents SHOULD be edited
├── comparison_reports/        # Generated analysis and test reports
├── test_cases.json           # Test case configuration and metadata
└── README.md                 # This file
```

## Quick Start

### 1. Add Your Test Documents

Copy your 3-document test case into the appropriate directories:

```bash
# Copy your starting document (with tracked changes)
cp "path/to/starting_doc.docx" input_documents/starting_doc_with_tracked_changes.docx

# Copy your fallback document  
cp "path/to/fallback_doc.docx" fallback_documents/clinical_trial_fallback.docx

# Copy your expected output document
cp "path/to/expected_doc.docx" expected_outputs/desired_edited_document.docx
```

### 2. Run the Test Framework

```bash
# From the project root directory
cd /mnt/c/Users/scb2/Documents/GitHub/word-doc-chatbot
python tests/golden_dataset_tests.py
```

### 3. Review Results

- Test reports will be generated in `comparison_reports/`
- Summary report: `comparison_reports/test_summary.md`
- Individual test reports: `comparison_reports/{test_case_id}_analysis_report.md`

## Test Case Configuration

Edit `test_cases.json` to add more test cases or modify existing ones:

```json
{
  "test_cases": [
    {
      "id": "case_001_clinical_trial_agreement",
      "description": "Your test case description",
      "input_document": "input_documents/your_input.docx",
      "fallback_document": "fallback_documents/your_fallback.docx", 
      "expected_output": "expected_outputs/your_expected.docx",
      "test_metadata": {
        "document_type": "legal_contract",
        "complexity": "high",
        "tracked_changes_present": true
      }
    }
  ]
}
```

## Testing Workflow

The framework follows this testing pipeline:

1. **Document Analysis**: Compare input, fallback, and expected documents
2. **Requirement Extraction**: Extract requirements from fallback document
3. **Instruction Generation**: Convert requirements to LLM instructions  
4. **Processing Simulation**: Apply instructions to input document
5. **Comparison Analysis**: Compare actual vs expected results
6. **Scoring**: Calculate translation quality metrics
7. **Reporting**: Generate detailed analysis reports

## Iterative Development

Use this framework for test-driven development:

1. **Morning**: Run baseline tests to see current performance
2. **Development**: Make improvements to translation algorithms
3. **Afternoon**: Test individual components  
4. **Evening**: Run full test suite and review results
5. **Analysis**: Identify patterns in failures and plan next improvements

## Success Metrics

Target metrics for production readiness:
- 90%+ match between generated and expected changes
- 95%+ requirement coverage from fallback documents  
- 85%+ instruction clarity score
- <10% false positive changes

## Files Overview

- `golden_dataset_tests.py`: Main testing framework
- `test_cases.json`: Test case configuration  
- `README.md`: This documentation
- `comparison_reports/`: Generated test reports and analysis

## Next Steps

1. Add your real test documents to the appropriate directories
2. Run the initial test to establish baseline metrics
3. Begin iterative development using the test feedback
4. Add more test cases as you create additional document pairs
5. Use the framework to validate improvements to the translation algorithm

---

For questions or issues, see the main DEVELOPMENT_ROADMAP.md for context and implementation details.