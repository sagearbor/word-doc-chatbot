# Quick Start Guide - Test Case Organization

## What Was Done

Your test .docx files have been organized into a clean, systematic structure:

### Before (Messy):
```
tests/fixtures/
├── test_main_document.docx          ❓ What is this?
├── test_fallback_requirements.docx  ❓ What does this relate to?
├── test_complex_fallback.docx       ❓ Which input does this use?
└── sample_fallback_contract.docx    ❓ Unused?

archive/debug_word_processor/
└── sample_input.docx                ❓ Has tracked changes?
```

### After (Organized):
```
tests/test_cases/
├── case_01_service_agreement/       ✅ Clear test case
│   ├── input/case_01_input_service_agreement.docx
│   ├── fallback/case_01_fallback_requirements.docx
│   ├── metadata.json                ✅ Documents expected changes
│   └── prompts/ (empty)
├── case_02_contract_editing/        ✅ Clear test case
│   ├── input/case_02_input_service_agreement.docx
│   ├── fallback/case_02_fallback_comprehensive_guidelines.docx
│   ├── metadata.json
│   └── prompts/ (empty)
└── case_03_existing_changes/        ✅ Clear test case
    ├── input/case_03_input_with_existing_changes.docx
    ├── prompts/case_03_prompt_additional_edits.txt
    ├── metadata.json
    └── fallback/ (empty)
```

## Your 3 Test Cases

### 🎯 Test Case 01: Service Agreement Tightening
**What:** Upload vague service agreement + requirements document → AI should make ~10 specific changes

**Files:**
- Input: `case_01_input_service_agreement.docx` (vague contract)
- Fallback: `case_01_fallback_requirements.docx` (10 requirements with "must/shall")
- Expected changes: 10 (documented in metadata.json)

**Currently:** System doesn't make all 10 changes - **this is what you want to fix!**

---

### 🎯 Test Case 02: Complex Contract Editing
**What:** Same input + complex requirements (some don't match input text) → AI should make ~9 changes

**Files:**
- Input: `case_02_input_service_agreement.docx` (same as case 01)
- Fallback: `case_02_fallback_comprehensive_guidelines.docx` (insurance, IP, etc.)
- Expected changes: 9+ (some need insertions, not replacements)

**Currently:** Harder test - some requirements have no matching text to replace

---

### 🎯 Test Case 03: Existing Tracked Changes ⚠️ CRITICAL
**What:** Doc with 8 existing tracked changes + prompt for 4 new changes → Should have 12 total

**Files:**
- Input: `case_03_input_with_existing_changes.docx` (**8 existing tracked changes!**)
- Prompt: `prompts/case_03_prompt_additional_edits.txt` (4 text instructions)
- Expected: 12 total changes (8 original preserved + 4 new)

**Critical:** Original 8 changes MUST NOT be lost!

---

## How to Test (Step by Step)

### 1. Start the application

```bash
# Terminal 1 (from project root)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 (from project root)
cd frontend-new && npm run dev
```

Open: http://localhost:5173

### 2. Run Test Case 01

1. Click "Upload Document" → select `tests/test_cases/case_01_service_agreement/input/case_01_input_service_agreement.docx`
2. Click "Upload Fallback Document" → select `tests/test_cases/case_01_service_agreement/fallback/case_01_fallback_requirements.docx`
3. Enable "Debug Mode" and "Extended Debug"
4. Click "Process Document"
5. Download the result
6. Open it and count how many tracked changes were actually made
7. Compare against the 10 expected changes in `metadata.json`

**Document results:**
```json
// In case_01_service_agreement/metadata.json, update:
"baseline_results": {
  "date": "2025-10-27",
  "changes_applied": 7,        // How many you counted
  "changes_missed": 3,          // 10 - 7 = 3 missed
  "missed_changes": [
    "Payment terms (change 3)",
    "Dispute resolution (change 10)"
  ],
  "success_rate": 0.70          // 7/10 = 0.70
}
```

### 3. Run Test Case 03 (Critical!)

1. Upload `case_03_input_with_existing_changes.docx`
2. **Do NOT upload fallback** - instead, copy/paste text from `prompts/case_03_prompt_additional_edits.txt` into the instructions box
3. Click "Process Document"
4. Download result
5. Open and verify:
   - ✅ All 8 original tracked changes still there?
   - ✅ How many of the 4 new changes were added?
6. **If any original changes lost = CRITICAL BUG**

---

## What You'll Learn from Testing

After running baseline tests, you'll have data like:

```
Case 01: 7/10 changes applied (70%) ⚠️
  Missed: changes 3, 8, 10

Case 02: 5/9 changes applied (56%) ⚠️
  Missed: changes with no direct text match

Case 03: 8 original + 3 new = 11/12 total (92%) ⚠️
  Missed: change 4 (counting sequence)
  Critical: ✅ All original changes preserved
```

This tells you:
- Which types of changes the AI struggles with
- Patterns in what gets missed (e.g., multi-word phrases, insertions)
- Where to focus improvement efforts

---

## Next: Iterative Improvement

### The Improvement Loop:

```
1. Test → Document what's missed
   ↓
2. Analyze → Find patterns
   ↓
3. Fix → Update word_processor.py or prompts
   ↓
4. Re-test → Measure improvement
   ↓
5. Repeat until success rate > 90%
```

### Common Issues and Fixes:

**Issue:** AI misses changes with phrases that span words
**Fix:** Improve fuzzy matching in `word_processor.py`

**Issue:** AI can't find text that's slightly different in doc
**Fix:** Improve contextual matching using surrounding text

**Issue:** AI doesn't know where to insert new clauses
**Fix:** Improve LLM prompt to better identify insertion points

---

## Files You Should Read

1. **`tests/test_cases/README.md`** - Complete testing guide
2. **`tests/test_cases/INVENTORY.md`** - All files documented
3. **`tests/TEST_CASES.md`** - Comprehensive test documentation
4. **`case_XX/metadata.json`** - Expected changes for each test

---

## Summary of Changes

✅ **Created organized structure** - 3 clear test cases
✅ **Documented expected changes** - 10, 9, and 12 changes respectively
✅ **Preserved original files** - Old locations still work
✅ **Added metadata** - JSON files with all test details
✅ **Created documentation** - 4 markdown files explaining everything

⚠️ **Your next step:** Run baseline tests and document results!

---

## Quick Commands

```bash
# View test case structure
tree tests/test_cases -L 2

# Find all test files
find tests/test_cases -name "*.docx" -o -name "*.txt"

# View metadata for case 01
cat tests/test_cases/case_01_service_agreement/metadata.json | jq

# Analyze case 03 existing changes via API
curl -X POST http://localhost:8000/analyze-document/ \
  -F "file=@tests/test_cases/case_03_existing_changes/input/case_03_input_with_existing_changes.docx"
```

---

## Questions?

See full documentation in:
- `tests/test_cases/README.md`
- `tests/TEST_CASES.md`

**You're ready to start systematic testing!** 🚀
