# Test Cases Documentation

## Overview

This document defines the test case organization system for the Word Document Chatbot. Each test case validates that the system correctly applies AI-suggested edits with tracked changes.

## Directory Structure

```
tests/test_cases/
├── case_01_service_agreement/
│   ├── input/                 # Main documents to be edited
│   ├── fallback/              # Fallback documents with requirements/instructions
│   ├── prompts/               # Text prompts (alternative to fallback docs)
│   ├── expected/              # Expected output documents
│   └── metadata.json          # Test case configuration
├── case_02_contract_editing/
│   └── ...
└── case_XX_description/
    └── ...
```

## Naming Convention

### File Naming Pattern

```
{test_case_id}_{file_type}_{description}.{ext}

Components:
- test_case_id: Matches parent directory (e.g., case_01, case_02)
- file_type: input, fallback, expected, prompt
- description: Brief content description (lowercase, underscores)
- ext: .docx for documents, .txt for prompts, .json for metadata
```

### Examples

```
case_01_input_service_agreement.docx         # Main document to edit
case_01_fallback_requirements.docx           # Requirements document
case_01_prompt_tighten_language.txt          # Alternative: typed prompt
case_01_expected_5_changes.docx              # Expected result (5 edits)
case_01_metadata.json                        # Test configuration
```

## Test Case Types

### Type 1: Fallback Document Processing
- **Input**: Main document with vague/incomplete language
- **Fallback**: Document containing requirements (must/shall/required)
- **Expected**: Document with tracked changes applied per requirements
- **Use case**: Legal document tightening, compliance updates

### Type 2: Text Prompt Processing
- **Input**: Main document to edit
- **Prompt**: Text instructions (simulates user typing in text box)
- **Expected**: Document with tracked changes applied per prompt
- **Use case**: Ad-hoc edits, quick corrections

### Type 3: Existing Tracked Changes
- **Input**: Document already containing tracked changes
- **Fallback/Prompt**: Additional edit instructions
- **Expected**: Document with BOTH original AND new tracked changes
- **Use case**: Iterative editing, review cycles

## Metadata Schema

Each test case directory contains a `metadata.json` file:

```json
{
  "test_case_id": "case_01",
  "description": "Service agreement language tightening",
  "type": "fallback_document",
  "created_date": "2025-10-27",
  "input_files": [
    {
      "filename": "case_01_input_service_agreement.docx",
      "description": "Service agreement with vague terms",
      "word_count": 115,
      "has_tracked_changes": false
    }
  ],
  "fallback_files": [
    {
      "filename": "case_01_fallback_requirements.docx",
      "description": "Mandatory requirements for service agreements",
      "word_count": 180,
      "requirement_keywords": {
        "must": 5,
        "shall": 2,
        "required": 1,
        "prohibited": 2
      }
    }
  ],
  "prompt_files": [],
  "expected_files": [
    {
      "filename": "case_01_expected_5_changes.docx",
      "description": "Service agreement with 5 tracked changes applied",
      "expected_changes_count": 5,
      "expected_changes": [
        {
          "change_number": 1,
          "old_text": "reasonable timeframe",
          "new_text": "within 30 business days",
          "reason": "Add specific deadline per requirement 1.1"
        },
        {
          "change_number": 2,
          "old_text": "may use subcontractors at their discretion",
          "new_text": "must obtain prior written approval before subcontracting",
          "reason": "Enforce subcontracting restriction per requirement 2.1"
        }
      ]
    }
  ],
  "test_configuration": {
    "author_name": "AI Assistant",
    "case_sensitive": true,
    "add_comments": true,
    "debug_mode": true
  },
  "validation_criteria": {
    "minimum_changes_required": 5,
    "all_requirements_addressed": true,
    "no_formatting_corruption": true,
    "tracked_changes_valid": true
  },
  "status": "active",
  "tags": ["legal", "contract", "requirements", "mandatory_language"]
}
```

## Current Test Cases

### Case 01: Service Agreement Tightening
- **Status**: Ready for organization
- **Input**: `test_main_document.docx` (115 words, vague contract language)
- **Fallback**: `test_fallback_requirements.docx` (180 words, 5 "must", 2 "shall")
- **Expected**: TBD (needs to be created or documented)
- **Expected Changes**: ~5-8 changes minimum
  1. Replace "reasonable timeframe" with specific deadline
  2. Add subcontracting restrictions
  3. Require weekly progress reports
  4. Enforce deliverable approval process
  5. Add confidentiality protections

### Case 02: Complex Contract Editing
- **Status**: Ready for organization
- **Input**: `test_main_document.docx` (reused)
- **Fallback**: `test_complex_fallback.docx` (203 words, 3 "must", 2 "shall")
- **Expected**: TBD
- **Expected Changes**: ~6-10 changes

### Case 03: Existing Tracked Changes
- **Status**: Ready for organization
- **Input**: `sample_input.docx` (73 words, **8 existing tracked changes**)
- **Fallback/Prompt**: TBD (needs to be created)
- **Expected**: TBD (should have 8 original + new changes)
- **Expected Changes**: Original 8 + additional changes

## Adding New Test Cases

### Step 1: Create Test Case Directory

```bash
# Create new test case structure
mkdir -p tests/test_cases/case_XX_description/{input,fallback,prompts,expected}
```

### Step 2: Add Test Documents

```bash
# Copy documents into appropriate subdirectories
cp your_input.docx tests/test_cases/case_XX_description/input/case_XX_input_name.docx
cp your_fallback.docx tests/test_cases/case_XX_description/fallback/case_XX_fallback_name.docx
```

### Step 3: Create Metadata

```bash
# Create metadata.json based on schema above
nano tests/test_cases/case_XX_description/metadata.json
```

### Step 4: Document Expected Changes

In the metadata, clearly document:
- Number of expected changes
- Specific old text → new text for each change
- Reason for each change
- Validation criteria

### Step 5: (Optional) Create Expected Output

Use the system to generate an expected output, manually verify it, then save:

```bash
# After manual verification
cp downloaded_output.docx tests/test_cases/case_XX_description/expected/case_XX_expected_N_changes.docx
```

## Running Tests

### Manual Testing

1. Start backend and frontend:
   ```bash
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   cd frontend-new && npm run dev
   ```

2. Test each case:
   - Upload input file from `input/` directory
   - Upload fallback file from `fallback/` directory (or type prompt from `prompts/`)
   - Download result
   - Compare against expected output in `expected/` directory
   - Verify all expected changes were applied

### Automated Testing (Future)

```bash
# Run test suite
python tests/run_test_cases.py

# Run specific test case
python tests/run_test_cases.py --case case_01

# Generate comparison reports
python tests/run_test_cases.py --compare --output tests/test_results/
```

## Test Result Documentation

For each test run, document:

```json
{
  "test_run_id": "run_2025_10_27_001",
  "test_case_id": "case_01",
  "timestamp": "2025-10-27T10:30:00Z",
  "results": {
    "total_expected_changes": 5,
    "actual_changes_applied": 3,
    "changes_matched": 3,
    "changes_missed": 2,
    "false_positive_changes": 0,
    "success_rate": 0.60
  },
  "missed_changes": [
    {
      "expected_change": 4,
      "old_text": "can be negotiated",
      "new_text": "shall be made within 15 days",
      "reason_missed": "Fuzzy match threshold not met"
    }
  ],
  "notes": "System struggles with phrases not clearly word-bounded"
}
```

## Iterative Improvement Workflow

1. **Baseline Test**: Run all test cases, document current accuracy
2. **Identify Patterns**: Analyze which types of changes are missed
3. **Improve Code**: Update word_processor.py, llm_handler.py, or prompts
4. **Retest**: Run test cases again
5. **Compare**: Measure improvement in success rate
6. **Document**: Update CLAUDE.md with findings
7. **Repeat**: Continue until target accuracy achieved (>90%)

## Success Metrics

Target performance metrics:
- **Change Detection Rate**: >90% of expected changes identified
- **Change Application Rate**: >95% of identified changes applied correctly
- **False Positive Rate**: <5% unexpected changes
- **Format Preservation**: 100% no document corruption
- **Tracked Changes Validity**: 100% valid XML structure

## Maintenance

### Weekly Tasks
- Review test case relevance
- Add new edge cases discovered
- Update expected outputs if system behavior intentionally changes
- Archive obsolete test cases

### After Code Changes
- Run full test suite
- Document any expected output changes
- Update test case metadata if behavior changes

## Notes for User

**Current Status**: Test files exist but need organization
- ✅ Input files identified
- ✅ Fallback files identified
- ⚠️ Expected outputs NOT yet defined
- ⚠️ Specific expected changes NOT yet documented

**Next Steps**:
1. For each test case, manually run the system and document:
   - How many changes SHOULD be made
   - What each change should be (old text → new text)
   - Why each change is needed
2. Create expected output files or document expected changes in metadata
3. Run baseline tests to measure current accuracy
4. Begin iterative improvement cycle

**Alternative**: Create new test files from scratch with:
- Clear, simple input documents
- Well-defined requirements in fallback documents
- Pre-documented expected changes
- Validated expected output files
