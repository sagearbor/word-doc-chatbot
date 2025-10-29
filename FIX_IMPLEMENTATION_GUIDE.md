# Quick Implementation Guide: Fix CONTEXT_AMBIGUOUS Failures

**Estimated Time:** 2-4 hours (including testing)
**Complexity:** Low
**Risk:** Minimal
**Files Changed:** 1 file, ~5 lines

---

## Step 1: Apply the Core Fix (10 minutes)

### File: `/dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot/backend/word_processor.py`

**Location:** Lines 313-315 in function `extract_tracked_changes_structured()`

**Current Code:**
```python
for para_idx, paragraph in enumerate(doc.paragraphs):
    # Build a map of the paragraph content to get context
    para_text = paragraph.text  # ← THIS IS THE PROBLEM

    # Track position in paragraph for context extraction
    current_pos = 0
```

**Fixed Code:**
```python
for para_idx, paragraph in enumerate(doc.paragraphs):
    # Build a map of the paragraph content to get context
    # Use same extraction method as process_document_with_edits for consistency
    para_text, _ = _build_visible_text_map(paragraph)

    # Track position in paragraph for context extraction
    current_pos = 0
```

**Why this works:**
- Ensures context extraction uses the same method as context matching
- Both phases now use `_build_visible_text_map()` consistently
- Handles tracked changes in both documents identically

---

## Step 2: Add a Comment Explaining the Fix (2 minutes)

Add this comment above the change:

```python
for para_idx, paragraph in enumerate(doc.paragraphs):
    # CRITICAL: Must use _build_visible_text_map() for consistency with
    # process_document_with_edits(). Using paragraph.text creates mismatch
    # when documents contain tracked changes, causing CONTEXT_AMBIGUOUS failures.
    # See: CONTEXT_AMBIGUOUS_ROOT_CAUSE_ANALYSIS.md
    para_text, _ = _build_visible_text_map(paragraph)
```

---

## Step 3: Test with JEx2 Documents (30-60 minutes)

### Test Command:
```bash
cd /dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot

# Option 1: Test via API endpoint
curl -X POST http://localhost:8000/process-document-with-fallback/ \
  -F "main_file=@tests/golden_dataset/dcri_examples/JEx2_CTA_INPUT_redlineFromSite.docx" \
  -F "fallback_file=@tests/golden_dataset/dcri_examples/JEx2_CTA_FALLBACK_byDcri.docx" \
  -F "user_instructions=Apply all changes from fallback" \
  -F "debug_mode=true"

# Option 2: Test directly with Python
python3 << 'EOF'
import sys
sys.path.append('/dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot')

from backend.word_processor import (
    extract_tracked_changes_structured,
    convert_tracked_changes_to_edits,
    process_document_with_edits
)

# Extract changes from fallback
fallback_path = "tests/golden_dataset/dcri_examples/JEx2_CTA_FALLBACK_byDcri.docx"
tracked_changes = extract_tracked_changes_structured(fallback_path)
print(f"Extracted {len(tracked_changes)} tracked changes")

# Convert to edits
edits = convert_tracked_changes_to_edits(tracked_changes)
print(f"Converted to {len(edits)} edits")

# Apply to main document
main_path = "tests/golden_dataset/dcri_examples/JEx2_CTA_INPUT_redlineFromSite.docx"
result = process_document_with_edits(
    main_path,
    "test_output.docx",
    edits,
    debug_mode=True
)

print(f"\nResult: {result}")
EOF
```

### Expected Results (Success Criteria):

**Before Fix:**
```
Applied: 0
CONTEXT_AMBIGUOUS: 11
SPECIFIC_TEXT_NOT_FOUND: 0
```

**After Fix (Target):**
```
Applied: 9-11  (82-100% success)
CONTEXT_AMBIGUOUS: 0-2  (only legitimate ambiguities)
SPECIFIC_TEXT_NOT_FOUND: 0
```

### What to Check:
1. ✅ Number of successfully applied edits increases dramatically
2. ✅ CONTEXT_AMBIGUOUS count drops to near zero
3. ✅ Output document contains tracked changes in correct locations
4. ✅ No crashes or exceptions
5. ✅ Processing time remains reasonable (< 10% slower)

---

## Step 4: Run Regression Tests (1-2 hours)

### Test Suite:
```bash
# Run all word processor tests
pytest tests/test_word_processor.py -v

# Run golden dataset tests
pytest tests/golden_dataset_tests.py -v

# Run main API tests
pytest tests/test_main.py -v

# Run with coverage
pytest tests/ --cov=backend/word_processor --cov-report=html
```

### Expected Results:
- ✅ All existing tests pass (no regressions)
- ✅ Code coverage remains high (>80%)
- ✅ No new failures introduced

### If Tests Fail:
1. Check if test expected values need updating (they may expect old behavior)
2. Verify the failure is not a genuine regression
3. Update test expectations if new behavior is correct

---

## Step 5: Edge Case Testing (Optional but Recommended, 30 minutes)

Test with various document types:

```bash
# Create test documents with:
# - Only tracked changes (no comments)
# - Only comments (no tracked changes)
# - Both tracked changes and comments
# - Multiple authors
# - Nested changes
```

Example test cases:
1. **Simple insertion:** Single word insertion with clear context
2. **Simple deletion:** Single word deletion
3. **Substitution:** Word replacement
4. **Empty paragraph:** Tracked change in empty paragraph
5. **Large insertion:** Multi-sentence insertion
6. **Multiple changes per paragraph:** Several changes close together

---

## Step 6: Performance Testing (Optional, 30 minutes)

Measure performance impact:

```python
import time
from backend.word_processor import extract_tracked_changes_structured

doc_path = "tests/golden_dataset/dcri_examples/JEx2_CTA_FALLBACK_byDcri.docx"

# Time the extraction
start = time.time()
for _ in range(10):
    changes = extract_tracked_changes_structured(doc_path)
end = time.time()

avg_time = (end - start) / 10
print(f"Average extraction time: {avg_time:.3f} seconds")
```

**Acceptable Performance:**
- Extraction time should be < 1 second for typical documents
- At most 10% slower than previous implementation
- No memory leaks or excessive memory usage

---

## Step 7: Update Documentation (15 minutes)

### File: `FALLBACK_TRACKED_CHANGES.md`

Add a section explaining the extraction method:

```markdown
## Technical Implementation Details

### Text Extraction Consistency

The system uses `_build_visible_text_map()` for all text extraction to ensure consistency:

1. **Context extraction** (from fallback document): Uses `_build_visible_text_map()`
2. **Context matching** (in main document): Uses `_build_visible_text_map()`

This consistency is critical because:
- Documents with tracked changes have multiple text representations
- `paragraph.text` produces different output than `_build_visible_text_map()`
- Using different methods causes context mismatch and CONTEXT_AMBIGUOUS failures

**Example:** A paragraph with tracked changes:
- `paragraph.text`: "...and _____________, located at _______________..."
- `_build_visible_text_map()`: "...and _ University of North Carolina..., located at Tarheel Road..."

Using inconsistent methods would cause context extracted from fallback to never match in main document.
```

---

## Step 8: Commit Changes (10 minutes)

```bash
cd /dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot

# Stage changes
git add backend/word_processor.py
git add FALLBACK_TRACKED_CHANGES.md
git add CONTEXT_AMBIGUOUS_ROOT_CAUSE_ANALYSIS.md
git add CONTEXT_MISMATCH_DIAGRAM.md
git add FIX_IMPLEMENTATION_GUIDE.md

# Commit with descriptive message
git commit -m "fix: Resolve CONTEXT_AMBIGUOUS failures in fallback document processing

- Use _build_visible_text_map() consistently in both extraction and application phases
- Previously used paragraph.text for extraction and _build_visible_text_map() for matching
- This inconsistency caused complete text mismatch when documents had tracked changes
- Fixes 0/11 success rate issue with JEx2 real-world test case
- Add comprehensive root cause analysis documentation

Resolves: CONTEXT_AMBIGUOUS failures for documents with tracked changes
Impact: Increases success rate from 0% to 82-100% for real-world cases
Files changed: backend/word_processor.py (1 line)
Testing: Verified with JEx2_CTA documents, all regression tests pass

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Rollback Plan (If Needed)

If the fix causes issues:

```bash
# Revert the commit
git revert HEAD

# Or manually change back
# In backend/word_processor.py line 315:
# Change back to: para_text = paragraph.text
```

---

## Verification Checklist

Before considering the fix complete:

- [ ] Code change applied (1 line in word_processor.py)
- [ ] Explanatory comment added
- [ ] JEx2 test case now succeeds (9-11/11 edits applied)
- [ ] All regression tests pass
- [ ] Performance impact acceptable (< 10% slower)
- [ ] Documentation updated
- [ ] Changes committed to git
- [ ] Docker container rebuilt (if using Docker)
- [ ] User notified of fix

---

## Expected Timeline

| Task | Time | Cumulative |
|------|------|------------|
| Apply core fix | 10 min | 10 min |
| Add documentation | 5 min | 15 min |
| Test with JEx2 | 30 min | 45 min |
| Run regression tests | 60 min | 1h 45m |
| Edge case testing | 30 min | 2h 15m |
| Update docs | 15 min | 2h 30m |
| Commit changes | 10 min | 2h 40m |
| **Total** | **2h 40m** | |

Add buffer for unexpected issues: **3-4 hours total**

---

## Success Metrics

The fix is successful when:

1. **Primary Goal:** JEx2 test case success rate increases to ≥ 82% (9/11 edits)
2. **No Regressions:** All existing tests continue to pass
3. **Performance:** Extraction time increases by ≤ 10%
4. **Documentation:** Clear explanation of why the fix works
5. **User Confirmation:** User verifies fix resolves their real-world issue

---

## Next Steps After Fix

1. Monitor for similar issues in other document types
2. Consider adding automated tests for this scenario
3. Document best practices for fallback document creation
4. Investigate if other text extraction inconsistencies exist
5. Consider creating a unified text extraction API to prevent future mismatches

---

## Contact for Questions

- See `CONTEXT_AMBIGUOUS_ROOT_CAUSE_ANALYSIS.md` for detailed technical explanation
- See `CONTEXT_MISMATCH_DIAGRAM.md` for visual representation
- Review git commit history for implementation details
- Check Docker logs for runtime behavior: `docker logs word-chatbot-sveltekit`
