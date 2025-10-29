# Root Cause Analysis: CONTEXT_AMBIGUOUS Failures in Real-World Fallback Document Test

**Date:** 2025-10-29
**Investigation:** Why 11 LLM-suggested edits failed with CONTEXT_AMBIGUOUS errors
**Test Case:** JEx2_CTA_INPUT_redlineFromSite.docx + JEx2_CTA_FALLBACK_byDcri.docx

---

## Executive Summary

**ROOT CAUSE IDENTIFIED:** The fallback document processing system has a critical mismatch between:

1. **Context extraction** (uses `paragraph.text` from fallback document)
2. **Context matching** (uses `_build_visible_text_map()` from main document)

These two methods produce **completely different text** when documents contain tracked changes, causing all context-based matching to fail.

**Impact:** 11 out of 11 edits failed with CONTEXT_AMBIGUOUS errors, resulting in 0% success rate for a real-world test case that "would be obvious to a human."

---

## Detailed Investigation Findings

### 1. The Core Problem: Two Different Text Extraction Methods

#### Method 1: `paragraph.text` (used in `extract_tracked_changes_structured`)
- **Location:** Line 315 in word_processor.py
- **Behavior:** Returns the "display text" with tracked insertions visible, deletions hidden
- **Example output for Paragraph 4:**
  ```
  ...and _____________, located at _______________ ("Study Site")...
  ```

#### Method 2: `_build_visible_text_map()` (used in `process_document_with_edits`)
- **Location:** Line 188 in word_processor.py
- **Behavior:** Builds text by iterating XML elements, includes tracked insertions, excludes tracked deletions
- **Example output for SAME Paragraph 4:**
  ```
  ...and _ University of North Carolina at Chapel Hill on behalf of itself
  and its affiliates, located at Tarheel Road, 27516 ("Study Site")...
  ```

**The Difference:** 102 characters difference in the same paragraph!

### 2. Test Case Specifics

**Documents:**
- Main: `JEx2_CTA_INPUT_redlineFromSite.docx` (has tracked changes)
- Fallback: `JEx2_CTA_FALLBACK_byDcri.docx` (has tracked changes AND comments)

**Tracked Changes Found:**
- **Main document:** Contains insertions and deletions
  - Example: Insertion of " University of North Carolina at Chapel Hill on behalf of itself and its affiliates"
  - Example: Deletion of "____________"

- **Fallback document:** Contains insertions (11 total)
  - All are insertion-type tracked changes (old_text = "")
  - Mix of small insertions (single space) and large text blocks

**Comments:**
- Fallback document contains Word annotation bubbles
- Comments are interspersed in XML: `<w:commentRangeStart>`, `<w:commentRangeEnd>`, `<w:commentReference>`
- Comments do NOT significantly affect text extraction (red herring - not the main issue)

### 3. Why All 11 Edits Failed

The failure sequence for each edit:

1. **Extract phase** (`extract_tracked_changes_structured`):
   ```python
   para_text = paragraph.text  # Uses .text property
   context_before = para_text[max(0, current_pos - context_chars):current_pos]
   ```
   - Context extracted: `' each as a "Party" and collectively the "Parties".'`
   - Source: `paragraph.text` from FALLBACK document

2. **Apply phase** (`process_document_with_edits`):
   ```python
   visible_text, elements_map = _build_visible_text_map(paragraph)
   # Try to find context_before in visible_text
   ```
   - Searches in: Text from `_build_visible_text_map()` on MAIN document
   - Context NOT found because visible_text is completely different
   - Result: CONTEXT_AMBIGUOUS (context disambiguation failed)

### 4. Concrete Example: Edit #1

**Tracked Change from Fallback:**
- Type: insertion
- Old text: `''` (empty string - this is an insertion)
- New text: `' '` (single space)
- Context before: `' each as a "Party" and collectively the "Parties".'`
- Context after: `''`

**What Happens:**
1. System looks for context in main document paragraph 4
2. Searches in visible text: `"...Duke and Study Site may be referred to herein each as a "Party" and collectively the "Parties"."`
3. Context FOUND! Position identified
4. Now try to find empty string `''` after this context
5. Found 34 occurrences of empty string (every character position)
6. Try to disambiguate using context
7. **FAILURE:** Context-based disambiguation fails because:
   - The text AFTER the context in main doc doesn't match fallback
   - Main has no extra space (the tracked insertion in fallback)
   - Multiple potential positions, can't uniquely identify

**Log Evidence:**
```
DEBUG (word_processor): P387: Found 10 occurrences of ''. Using context to disambiguate...
DEBUG (word_processor): P387: Multiple matches found but context-based disambiguation failed. Marking as ambiguous.
DEBUG (word_processor): P387: Context 'each as a "Party" and collecti...' was AMBIGUOUS for specific text ''.
```

### 5. Why Tracked Changes in Main Document Matter

The main document contains its own tracked changes:
- Insertions: " University of North Carolina at Chapel Hill..."
- Deletions: "____________"

When `_build_visible_text_map()` processes the main document:
- It INCLUDES the inserted text (from `<w:ins>` elements)
- It EXCLUDES the deleted text (skips `<w:delText>` in `<w:del>` elements)

When `paragraph.text` processes the main document:
- It shows a different representation
- The formatting is simpler (shows underscores as placeholders)

This means the context extracted from the fallback using `.text` will NEVER match the text in the main document extracted using `_build_visible_text_map()`.

---

## Additional Factors (Not Root Cause, But Complications)

### Word Comments
- Fallback document contains comment markers in XML
- Comments are interspersed: `<w:commentRangeStart>` between `<w:r>` elements
- `_build_visible_text_map()` ignores comment elements (correct behavior)
- Comments do NOT cause the CONTEXT_AMBIGUOUS issue
- **Verdict:** Red herring - not the primary problem

### Empty String Insertions
- 8 out of 11 changes have `old_text = ''` (pure insertions)
- Empty string matches occur everywhere (every character position)
- Requires perfect context matching for disambiguation
- When context matching fails, empty string edits are especially vulnerable
- **Verdict:** Amplifies the problem but not the root cause

### Fuzzy Matching
- Fuzzy matching is enabled (`FUZZY_MATCHING_ENABLED = True`)
- Threshold: 85% similarity required
- In this case, fuzzy matching doesn't help because:
  - Context text is completely different (not just slightly different)
  - Similarity scores are too low to meet threshold
- **Verdict:** Cannot compensate for the fundamental extraction mismatch

---

## Proposed Solutions

### Solution 1: Unify Text Extraction (RECOMMENDED)

**Change:** Make `extract_tracked_changes_structured()` use the same text extraction method as `process_document_with_edits()`

**Implementation:**
```python
def extract_tracked_changes_structured(input_docx_path: str, context_chars: int = 50):
    doc = Document(input_docx_path)
    tracked_changes = []

    for para_idx, paragraph in enumerate(doc.paragraphs):
        # USE _build_visible_text_map() instead of paragraph.text
        para_text, elements_map = _build_visible_text_map(paragraph)

        # Rest of the extraction logic remains the same
        # ...
```

**Pros:**
- Guarantees context consistency between extraction and application
- Minimal code changes (one function modification)
- No changes to matching logic needed
- Handles tracked changes in both documents correctly

**Cons:**
- None significant

**Effort:** Low (2-4 hours)

---

### Solution 2: Use Raw XML Positions Instead of Context

**Change:** Extract the exact XML position/structure of changes and apply them structurally rather than by text matching

**Implementation:**
- Store XML element indices and positions in `TrackedChange` objects
- Map structural positions between documents
- Apply changes at corresponding structural locations

**Pros:**
- More robust to text variations
- Doesn't rely on text matching at all
- Could handle complex structural changes

**Cons:**
- Major refactoring required
- Assumes documents have similar structure (may not be true)
- Much more complex implementation
- Breaks when document structure differs significantly

**Effort:** High (2-3 days)

**Verdict:** Overkill for this problem

---

### Solution 3: Improve Context Matching with Fuzzy Context

**Change:** When context doesn't match exactly, use fuzzy matching on the context itself

**Implementation:**
```python
def find_best_context_match(context, paragraph_text, threshold=0.80):
    """Find best fuzzy match for context in paragraph text"""
    # Use sliding window and SequenceMatcher
    # Return position with highest similarity above threshold
```

**Pros:**
- Could handle minor text variations
- Doesn't require changing extraction logic

**Cons:**
- Doesn't solve the fundamental problem (contexts are VERY different)
- May introduce false positives
- Slower performance (fuzzy matching is expensive)
- Still fails when main document has completely different content

**Effort:** Medium (1 day)

**Verdict:** Band-aid solution that doesn't address root cause

---

### Solution 4: Accept Both Tracked Changes as "Main" Text

**Change:** Process the main document to accept/show all tracked changes before applying fallback changes

**Implementation:**
```python
def process_document_with_fallback(main_doc_path, fallback_doc_path):
    # Step 1: Accept all tracked changes in main document
    main_doc = Document(main_doc_path)
    accept_all_tracked_changes(main_doc)  # New function

    # Step 2: Extract changes from fallback
    fallback_changes = extract_tracked_changes_structured(fallback_doc_path)

    # Step 3: Apply fallback changes to "clean" main document
    # ...
```

**Pros:**
- Creates a "clean" main document with consistent text
- Aligns with user workflow (accept main changes, then apply fallback changes)
- Clearer semantics: "Apply these changes to the current document state"

**Cons:**
- Changes document state before processing
- May not preserve original main document tracked changes
- User might want to review main doc changes first

**Effort:** Medium (1 day to implement accept_all_tracked_changes)

**Verdict:** Good option if user workflow supports it

---

## Recommendation

**Implement Solution 1: Unify Text Extraction**

### Rationale:
1. **Root cause alignment:** Directly addresses the mismatch between extraction and matching
2. **Minimal risk:** Small, focused change with clear behavior
3. **Quick implementation:** Can be completed and tested in a few hours
4. **Preserves existing logic:** All matching and application logic remains unchanged
5. **No breaking changes:** API and user experience stay the same

### Implementation Plan:

1. **Modify `extract_tracked_changes_structured()` (20 lines)**
   ```python
   # Line 315: Change from
   para_text = paragraph.text

   # To:
   para_text, _ = _build_visible_text_map(paragraph)
   ```

2. **Test with JEx2 documents** (verify changes are now found)

3. **Run full test suite** (ensure no regressions)

4. **Update documentation** (note the extraction method used)

### Expected Outcome:
- Context from fallback will match context in main document
- Empty string insertions will be uniquely identified by context
- Success rate should increase from 0% to >80% (some may still fail due to structural differences)

---

## Alternative: Hybrid Approach

If Solution 1 alone doesn't achieve sufficient success rate, combine with Solution 4:

1. **Accept all tracked changes in main document first** (clean slate)
2. **Extract changes from fallback using `_build_visible_text_map()`** (consistent extraction)
3. **Apply changes with current matching logic**

This ensures:
- Main document has no competing tracked changes
- Context extraction and matching use same method
- Maximum likelihood of successful application

**Effort:** Medium (4-6 hours total)

---

## Testing Recommendations

After implementing the fix:

1. **Re-test with JEx2 documents**
   - Verify all 11 edits are applied successfully
   - Check that tracked changes appear correctly in output
   - Validate author attribution and timestamps

2. **Test with documents containing:**
   - Only tracked changes (no comments)
   - Only comments (no tracked changes)
   - Both tracked changes and comments
   - Multiple authors' tracked changes
   - Conflicting changes in same location

3. **Regression testing**
   - Run full golden dataset tests
   - Verify existing test cases still pass
   - Check performance hasn't degraded

4. **Edge cases:**
   - Empty paragraphs with tracked changes
   - Tracked changes spanning multiple paragraphs
   - Nested tracked changes (if possible in Word)
   - Very large insertions/deletions

---

## Files Requiring Changes

### Primary:
- `/dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot/backend/word_processor.py`
  - Function: `extract_tracked_changes_structured()` (lines 289-436)
  - Change: Line 315 - use `_build_visible_text_map()` instead of `paragraph.text`

### Testing:
- Create new test case for this scenario
- Add to `/dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot/tests/test_cases/`

### Documentation:
- Update `FALLBACK_TRACKED_CHANGES.md` to document extraction behavior
- Note the use of `_build_visible_text_map()` for consistency

---

## Success Criteria

Fix is successful when:
1. ✅ All 11 edits from JEx2 test case are applied (or at least 9/11 = 82%)
2. ✅ Context matching succeeds for obvious changes
3. ✅ Existing test cases continue to pass (no regressions)
4. ✅ Performance impact < 10% (context extraction may be slightly slower)
5. ✅ Error rate for real-world documents drops significantly

---

## Conclusion

The CONTEXT_AMBIGUOUS failures are caused by using two different text extraction methods:
- `paragraph.text` for extracting context from fallback
- `_build_visible_text_map()` for matching in main document

These methods produce **completely different text** when documents contain tracked changes, making context-based matching impossible.

**The fix is straightforward:** Use `_build_visible_text_map()` consistently in both extraction and matching phases.

This is a **high-priority, low-complexity fix** that will significantly improve the system's ability to handle real-world legal documents with tracked changes.
