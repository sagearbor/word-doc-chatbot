# Test Cases Directory

This directory contains organized test cases for the Word Document Chatbot. Each test case validates the system's ability to apply AI-suggested edits with tracked changes.

## Quick Start

### Running a Test Case Manually

1. **Start the application:**
   ```bash
   # Terminal 1: Backend
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

   # Terminal 2: Frontend
   cd frontend-new && npm run dev
   ```

2. **Open frontend:** http://localhost:5173

3. **Test Case 01 Example:**
   - Upload `case_01_service_agreement/input/case_01_input_service_agreement.docx` as main file
   - Upload `case_01_service_agreement/fallback/case_01_fallback_requirements.docx` as fallback file
   - Click "Process Document"
   - Download result and compare against expected changes in `metadata.json`

4. **Document results** in the test case's `metadata.json` under `baseline_results`

### Directory Structure

```
test_cases/
├── README.md (this file)
├── case_01_service_agreement/
│   ├── input/              # Main documents to edit
│   ├── fallback/           # Fallback requirement documents
│   ├── prompts/            # Text prompts (alternative to fallback)
│   ├── expected/           # Expected output documents
│   └── metadata.json       # Test case configuration
├── case_02_contract_editing/
└── case_03_existing_changes/
```

## Test Cases Overview

### Case 01: Service Agreement Tightening ⭐ PRIMARY TEST
**Status:** Ready to test
**Priority:** High
**Type:** Fallback document processing

**What it tests:**
- Basic fallback document to LLM instruction conversion
- Requirement keyword extraction (must, shall, required, prohibited)
- Text replacement with tracked changes
- Vague → specific language conversion

**Files:**
- Input: `case_01_input_service_agreement.docx` (115 words, generic contract)
- Fallback: `case_01_fallback_requirements.docx` (180 words, 10 requirements)
- Expected: TBD - user needs to define or create expected output

**Expected changes:** ~10 changes (documented in metadata.json)

**How to test:**
1. Upload both files to frontend
2. Process with debug mode enabled
3. Download result
4. Verify each expected change from metadata.json
5. Document: How many changes applied? Which ones missed?

---

### Case 02: Complex Contract Editing
**Status:** Ready to test
**Priority:** Medium
**Type:** Fallback document with requirements beyond input scope

**What it tests:**
- Handling requirements with no direct text match (e.g., insurance clause)
- Complex requirement interpretation
- Insertion vs. replacement decisions
- Performance with comprehensive guidelines

**Files:**
- Input: `case_02_input_service_agreement.docx` (115 words, same as case_01)
- Fallback: `case_02_fallback_comprehensive_guidelines.docx` (203 words, advanced requirements)
- Expected: TBD

**Expected changes:** ~9+ changes (some may need insertions rather than replacements)

**Known challenges:**
- Some requirements (insurance, IP ownership) have no matching text in input
- System must decide WHERE to insert vs. what to replace
- Lower success threshold expected (70%)

---

### Case 03: Existing Tracked Changes ⭐ CRITICAL
**Status:** Ready to test
**Priority:** High
**Type:** Text prompt with document containing existing changes

**What it tests:**
- Preservation of existing tracked changes
- Iterative editing capability
- Multi-author workflow support
- XML integrity with mixed changes

**Files:**
- Input: `case_03_input_with_existing_changes.docx` (73 words, **8 existing tracked changes**)
- Prompt: `prompts/case_03_prompt_additional_edits.txt` (4 new edit instructions)
- Expected: TBD - should have 8 original + 4 new = 12 total changes

**CRITICAL requirement:** All 8 original tracked changes MUST be preserved

**How to test:**
1. First, analyze input file to document the 8 existing changes:
   ```bash
   # Use backend endpoint
   curl -X POST http://localhost:8000/analyze-document/ \
     -F "file=@tests/test_cases/case_03_existing_changes/input/case_03_input_with_existing_changes.docx"
   ```
2. Upload file and paste prompt text (not fallback document)
3. Process and download
4. Verify: All 8 original changes still present + 4 new changes added
5. **If any original changes lost = TEST FAILED**

---

## Test File Naming Convention

```
{test_case_id}_{file_type}_{description}.{ext}

Examples:
✅ case_01_input_service_agreement.docx
✅ case_01_fallback_requirements.docx
✅ case_02_expected_12_changes.docx
✅ case_03_prompt_additional_edits.txt

❌ test_file.docx (no case ID)
❌ mytest.docx (not descriptive)
❌ Input File.docx (spaces, not lowercase)
```

## Metadata Schema

Each test case includes `metadata.json` with:
- Test case description and type
- Input/fallback/prompt file documentation
- **Expected changes** (old text → new text, with reasons)
- Validation criteria and success thresholds
- Known issues and testing notes
- Baseline results (to be filled in during testing)

See `case_01_service_agreement/metadata.json` for complete example.

## Adding New Test Cases

```bash
# 1. Create directory structure
mkdir -p tests/test_cases/case_XX_description/{input,fallback,prompts,expected}

# 2. Copy test files
cp your_input.docx tests/test_cases/case_XX_description/input/case_XX_input_name.docx
cp your_fallback.docx tests/test_cases/case_XX_description/fallback/case_XX_fallback_name.docx

# 3. Create metadata.json
# Copy template from case_01 and modify

# 4. Document expected changes in metadata.json
# Be specific: old_text → new_text for each change
```

## Testing Workflow

### 1. Baseline Testing (First Run)
```
For each test case:
├── Run test manually through frontend
├── Download result
├── Count changes applied
├── Identify missed changes
├── Document in metadata.json baseline_results:
    {
      "date": "2025-10-27",
      "changes_applied": 7,
      "changes_missed": 3,
      "success_rate": 0.70
    }
```

### 2. Iterative Improvement
```
1. Review baseline results
2. Identify patterns in missed changes
3. Update word_processor.py or llm_handler.py
4. Re-run tests
5. Compare new success_rate vs baseline
6. Repeat until success_rate > 0.90
```

### 3. Documentation
After each test run, update:
- Metadata `baseline_results` section
- Known issues if new problems discovered
- Success threshold if expectations need adjustment

## Success Metrics

**Target Performance (after iterative improvement):**
- Case 01: >90% success rate (9+/10 changes)
- Case 02: >70% success rate (7+/9 changes) - harder due to insertions
- Case 03: 100% preservation of original changes + >75% new changes

**Current Status:** Awaiting baseline testing

## Automated Testing (Future Enhancement)

```bash
# Future: Automated test runner
python tests/run_test_cases.py --all
python tests/run_test_cases.py --case case_01
python tests/run_test_cases.py --baseline  # Record baseline metrics
python tests/run_test_cases.py --compare   # Compare against baseline
```

## Files Reference

### Original Test Files (Preserved)
These files remain in original locations for backwards compatibility:
- `tests/fixtures/test_main_document.docx`
- `tests/fixtures/test_fallback_requirements.docx`
- `tests/fixtures/test_complex_fallback.docx`
- `tests/fixtures/sample_fallback_contract.docx` (unused currently)
- `archive/debug_word_processor/sample_input.docx`

### New Organized Structure
Test files are now **copied** (not moved) to organized structure in `tests/test_cases/`.

## Next Steps for User

### Immediate Tasks:
1. **Run baseline tests** for all 3 cases
2. **Document actual results** in each metadata.json
3. **Identify patterns** in missed changes
4. **Create expected output files** (optional but helpful):
   - Manually verify a good output
   - Save to `expected/` directory
   - Use for visual comparison

### For Better Testing:
Consider creating **expected output .docx files**:
```bash
# After verifying a processed output is correct
cp processed_output.docx tests/test_cases/case_01_service_agreement/expected/case_01_expected_10_changes.docx
```

This allows visual diff comparison later.

## Questions?

See main documentation:
- `tests/TEST_CASES.md` - Comprehensive testing guide
- `CLAUDE.md` - Project overview
- `backend/word_processor.py` - Core document processing logic

## Summary

✅ 3 test cases ready
✅ All metadata documented
✅ Naming convention established
⚠️ Expected outputs need to be defined by user
⚠️ Baseline testing not yet performed

**Ready for iterative testing to improve AI accuracy!**
