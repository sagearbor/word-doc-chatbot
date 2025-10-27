# Test Files Inventory

**Last Updated:** 2025-10-27
**Branch:** test-file-organization

## Summary

**Total Test Cases:** 3
**Total Test Files:** 8 files (5 .docx + 1 .txt + 1 JSON + 1 metadata files)
**Organization Status:** ✅ Complete
**Baseline Testing Status:** ⚠️ Not yet performed

---

## File Mapping: Old → New

### Original Test Files (Preserved for Compatibility)

| Original Location | New Location | Purpose |
|------------------|--------------|---------|
| `tests/fixtures/test_main_document.docx` | `case_01_service_agreement/input/case_01_input_service_agreement.docx` | Input doc for case 01 |
| `tests/fixtures/test_main_document.docx` | `case_02_contract_editing/input/case_02_input_service_agreement.docx` | Input doc for case 02 (reused) |
| `tests/fixtures/test_fallback_requirements.docx` | `case_01_service_agreement/fallback/case_01_fallback_requirements.docx` | Fallback for case 01 |
| `tests/fixtures/test_complex_fallback.docx` | `case_02_contract_editing/fallback/case_02_fallback_comprehensive_guidelines.docx` | Fallback for case 02 |
| `archive/debug_word_processor/sample_input.docx` | `case_03_existing_changes/input/case_03_input_with_existing_changes.docx` | Input with existing changes |

### Unused Files

| File | Status | Notes |
|------|--------|-------|
| `tests/fixtures/sample_fallback_contract.docx` | **Unused** | Not currently assigned to test case. Could be used for case_04 in future. |

---

## Test Case 01: Service Agreement Tightening

### Files
```
case_01_service_agreement/
├── input/
│   └── case_01_input_service_agreement.docx      [37 KB, 115 words, 9 paragraphs]
├── fallback/
│   └── case_01_fallback_requirements.docx        [37 KB, 180 words, 13 paragraphs]
├── prompts/
│   └── (empty - uses fallback document instead)
├── expected/
│   └── (TBD - user needs to create/define)
└── metadata.json                                  [7.4 KB]
```

### File Details

**Input: case_01_input_service_agreement.docx**
- Source: `tests/fixtures/test_main_document.docx`
- Content: Generic service agreement with 4 sections
- Characteristics: Vague language ("should", "may", "can be negotiated")
- Tracked changes: None
- Purpose: Base document to be tightened with specific requirements

**Fallback: case_01_fallback_requirements.docx**
- Source: `tests/fixtures/test_fallback_requirements.docx`
- Content: Mandatory requirements document
- Sections: Mandatory Requirements, Prohibited Activities, Additional Requirements
- Keywords: 5 "must", 2 "shall", 1 "required", 2 "prohibited"
- Purpose: Provides specific requirements to apply to input document

**Expected output:** TBD - ~10 changes expected

---

## Test Case 02: Complex Contract Editing

### Files
```
case_02_contract_editing/
├── input/
│   └── case_02_input_service_agreement.docx      [37 KB, 115 words, 9 paragraphs]
├── fallback/
│   └── case_02_fallback_comprehensive_guidelines.docx  [37 KB, 203 words, 14 paragraphs]
├── prompts/
│   └── (empty - uses fallback document instead)
├── expected/
│   └── (TBD - user needs to create/define)
└── metadata.json                                  [6.1 KB]
```

### File Details

**Input: case_02_input_service_agreement.docx**
- Source: `tests/fixtures/test_main_document.docx` (same as case_01)
- Content: Same generic service agreement
- Note: Testing how system handles more complex requirements than input addresses
- Tracked changes: None

**Fallback: case_02_fallback_comprehensive_guidelines.docx**
- Source: `tests/fixtures/test_complex_fallback.docx`
- Content: Comprehensive contract editing guidelines
- Sections: Critical Requirements (insurance, IP, records), Performance Standards, Restrictions
- Keywords: 3 "must", 2 "shall", 2 "required", 1 "prohibited"
- Special features: Requirements that don't map to existing input text (insurance, IP ownership)
- Purpose: Tests system's ability to handle complex, non-matching requirements

**Expected output:** TBD - ~9+ changes expected (some insertions, not just replacements)

---

## Test Case 03: Existing Tracked Changes

### Files
```
case_03_existing_changes/
├── input/
│   └── case_03_input_with_existing_changes.docx  [37 KB, 73 words, 11 paragraphs]
├── fallback/
│   └── (empty - uses text prompt instead)
├── prompts/
│   └── case_03_prompt_additional_edits.txt       [0.4 KB, 4 instructions]
├── expected/
│   └── (TBD - should have 8 original + 4 new = 12 changes)
└── metadata.json                                  [4.8 KB]
```

### File Details

**Input: case_03_input_with_existing_changes.docx**
- Source: `archive/debug_word_processor/sample_input.docx`
- Content: Simple test document
- **Tracked changes: 8 existing changes** (insertions, deletions, substitutions)
- Existing changes include: number edits, sentence additions, counting modifications
- Purpose: Test preservation of existing tracked changes during new editing

**Prompt: case_03_prompt_additional_edits.txt**
- Content: 4 text replacement instructions
  1. "simple file" → "test document"
  2. "program can work" → "system functions correctly"
  3. Add "successfully" before "change this sentence"
  4. Change count to 15 instead of 10
- Purpose: Simulates user typing instructions in text box (alternative to fallback doc)

**Expected output:** TBD
- Must preserve all 8 original tracked changes
- Add 4 new tracked changes from prompt
- Total: 12 tracked changes

**Critical requirement:** Original changes MUST NOT be lost

---

## File Statistics

### By File Type
- **.docx files:** 5 (3 unique, 2 copies)
- **.txt files:** 1 (prompt)
- **.json files:** 3 (metadata)
- **Total:** 9 files across 3 test cases

### By Role
- **Input documents:** 3 files
- **Fallback documents:** 2 files
- **Prompt files:** 1 file
- **Expected outputs:** 0 files (TBD)
- **Metadata:** 3 files

### Content Characteristics

| Document | Words | Paragraphs | Has Tracked Changes | Requirement Keywords |
|----------|-------|------------|---------------------|---------------------|
| case_01_input | 115 | 9 | No | should: 2 |
| case_01_fallback | 180 | 13 | No | must: 5, shall: 2, required: 1, prohibited: 2 |
| case_02_input | 115 | 9 | No | should: 2 |
| case_02_fallback | 203 | 14 | No | must: 3, shall: 2, required: 2, prohibited: 1 |
| case_03_input | 73 | 11 | **Yes (8)** | should: 1 |

---

## Test Case Relationships

```
Input Document (test_main_document.docx)
├─→ Case 01: + Fallback (test_fallback_requirements.docx)
│   Expected: ~10 changes
│
└─→ Case 02: + Fallback (test_complex_fallback.docx)
    Expected: ~9+ changes

Input Document (sample_input.docx with 8 existing changes)
└─→ Case 03: + Prompt (text instructions)
    Expected: 8 original + 4 new = 12 changes
```

---

## Backwards Compatibility

### Original File Locations (Preserved)

The following files remain in their original locations and are still referenced by existing test scripts:

```
tests/fixtures/
├── test_main_document.docx          ← Still here (not moved, only copied)
├── test_fallback_requirements.docx  ← Still here
├── test_complex_fallback.docx       ← Still here
└── sample_fallback_contract.docx    ← Still here (unused)

archive/debug_word_processor/
└── sample_input.docx                ← Still here
```

**Note:** Files were **copied**, not moved, to maintain compatibility with existing test scripts like `test_fallback_processing.py` which reference the original paths.

---

## Test Scripts to Update

The following test scripts may need path updates to use new organized structure:

1. **tests/test_fallback_processing.py**
   - Currently uses `create_test_documents.py` to generate files on-the-fly
   - Could be updated to use organized test cases
   - Status: ⚠️ Still uses old approach (dynamic generation)

2. **tests/create_test_documents.py**
   - Creates test files programmatically
   - Could be kept for reference or updated to generate into test_cases/ structure
   - Status: ⚠️ Still generates to current directory

3. **tests/golden_dataset_tests.py**
   - Uses `tests/golden_dataset/` structure (separate from test_cases/)
   - Status: ✅ No changes needed (different test framework)

**Recommendation:** Keep original test scripts working for now. New tests can reference `tests/test_cases/` structure.

---

## Next Steps

### For User:
1. ✅ Review organized test case structure
2. ⚠️ **Run baseline tests** for all 3 cases using frontend
3. ⚠️ **Document results** in each `metadata.json` under `baseline_results`
4. ⚠️ **Create or define expected outputs** for each test case
5. ⚠️ Begin iterative improvement based on test results

### For Future Development:
1. Create automated test runner script (`run_test_cases.py`)
2. Add visual diff comparison tool for expected vs actual outputs
3. Create test case 04 using `sample_fallback_contract.docx`
4. Build CI/CD integration for automatic regression testing
5. Add test coverage metrics dashboard

---

## Appendix: Quick Reference

### Test Case IDs
- `case_01` - Service Agreement Tightening (primary test)
- `case_02` - Complex Contract Editing
- `case_03` - Existing Tracked Changes (critical test)

### Command to List All Test Files
```bash
cd tests/test_cases
find . -name "*.docx" -o -name "*.txt" -o -name "metadata.json" | sort
```

### Command to Check File Sizes
```bash
cd tests/test_cases
du -h */input/*.docx */fallback/*.docx 2>/dev/null
```

### Command to Extract Existing Changes from Case 03
```bash
# Use backend API to analyze case_03 input
curl -X POST http://localhost:8000/analyze-document/ \
  -F "file=@tests/test_cases/case_03_existing_changes/input/case_03_input_with_existing_changes.docx"
```

---

**End of Inventory**
