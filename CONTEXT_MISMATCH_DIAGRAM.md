# Visual Diagram: Context Mismatch Problem

## The Problem in One Image

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FALLBACK DOCUMENT                                   │
│                    (JEx2_CTA_FALLBACK_byDcri.docx)                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ extract_tracked_changes_structured()
                                    │ Uses: paragraph.text
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  Extracted Context:                                                         │
│  "...and _____________, located at _______________ (Study Site)..."        │
│                                                                             │
│  Tracked Change:                                                            │
│    old_text: "" (empty - insertion)                                        │
│    new_text: " " (single space)                                            │
│    context_before: 'each as a "Party" and collectively the "Parties".'     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Send to apply phase
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MAIN DOCUMENT                                     │
│                    (JEx2_CTA_INPUT_redlineFromSite.docx)                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ process_document_with_edits()
                                    │ Uses: _build_visible_text_map()
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  Main Document Visible Text:                                               │
│  "...and _ University of North Carolina at Chapel Hill on behalf of        │
│   itself and its affiliates, located at Tarheel Road, 27516 (Study Site)..." │
│                                                                             │
│  Trying to find context:                                                   │
│    'each as a "Party" and collectively the "Parties".'                     │
│                                                                             │
│  ❌ Context NOT FOUND or text after context doesn't match!                 │
│  ❌ Result: CONTEXT_AMBIGUOUS                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## The Root Cause

### Extraction Phase (from Fallback)
```python
# In extract_tracked_changes_structured() - Line 315
para_text = paragraph.text  # ← Uses .text property
context_before = para_text[max(0, current_pos - context_chars):current_pos]
```

**What `paragraph.text` returns:**
- Standard text representation
- Shows "____________" as placeholders
- Example: `"...and _____________, located at _______________ ("Study Site")..."`

---

### Application Phase (to Main)
```python
# In process_document_with_edits()
visible_text, elements_map = _build_visible_text_map(paragraph)  # ← Different method!
# Try to find context in visible_text
```

**What `_build_visible_text_map()` returns:**
- Iterates through XML elements
- Includes tracked insertions: `<w:ins>` → visible text
- Excludes tracked deletions: `<w:del>` → skipped
- Example: `"...and _ University of North Carolina at Chapel Hill on behalf of itself and its affiliates, located at Tarheel Road, 27516 ("Study Site")..."`

---

## Side-by-Side Comparison

| Aspect | Fallback (extraction) | Main (application) |
|--------|----------------------|-------------------|
| Method | `paragraph.text` | `_build_visible_text_map()` |
| Line | 315 | 188 |
| Text | "...and _____________, located at _______________..." | "...and _ University of North Carolina at Chapel Hill on behalf of itself and its affiliates, located at Tarheel Road, 27516..." |
| Length | 449 chars | 551 chars |
| Difference | - | **+102 chars** |
| Context Match | ❌ | Context extracted from fallback doesn't exist in main! |

---

## Why ALL 11 Edits Failed

```
Edit #1: Insert " " after "Parties"
   ↓
   Extract context from fallback: "...Parties."
   ↓
   Search in main document visible text: "...Parties."
   ↓
   Context found! But what comes next in main ≠ what comes next in fallback
   ↓
   Try to disambiguate empty string "" insertion
   ↓
   Found 34 positions (empty string matches everywhere)
   ↓
   ❌ Context-based disambiguation FAILED
   ↓
   Result: CONTEXT_AMBIGUOUS

Edit #2: Insert " that are reflected..."
   Same failure pattern
   ↓
   ❌ CONTEXT_AMBIGUOUS

Edit #3-11: All follow same failure pattern
   ↓
   ❌ 0/11 edits applied successfully
```

---

## The Fix (Solution 1)

### Change ONE line in `extract_tracked_changes_structured()`:

```python
# BEFORE (Line 315):
para_text = paragraph.text

# AFTER:
para_text, _ = _build_visible_text_map(paragraph)
```

### Result:
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  EXTRACTION (from Fallback)                                                 │
│  Uses: _build_visible_text_map()                                           │
│  Text: "...and _ University of North Carolina at Chapel Hill..."           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│  APPLICATION (to Main)                                                      │
│  Uses: _build_visible_text_map()                                           │
│  Text: "...and _ University of North Carolina at Chapel Hill..."           │
│                                                                             │
│  ✅ Context MATCHES!                                                        │
│  ✅ Edits successfully applied                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Why Comments Are NOT the Problem

Initial hypothesis: Word comments interfere with text extraction

**Reality:** Comments are interspersed in XML but properly handled:
```xml
<w:p>
  <w:r><w:t>...each as a "Party" and collectively the "</w:t></w:r>
  <w:commentRangeStart w:id="0"/>    ← Comment marker
  <w:r><w:t>Parties</w:t></w:r>      ← Text inside comment
  <w:commentRangeEnd w:id="0"/>      ← Comment end
  <w:r><w:t>".</w:t></w:r>
  <w:ins w:author="JoAnna">          ← Tracked insertion
    <w:r><w:t> </w:t></w:r>
  </w:ins>
</w:p>
```

`_build_visible_text_map()` correctly:
- ✅ Includes text from `<w:r>` elements (even inside comment ranges)
- ✅ Includes text from `<w:ins>` elements (tracked insertions)
- ✅ Excludes `<w:del>` elements (tracked deletions)
- ✅ Ignores comment markers (`<w:commentRangeStart>`, etc.)

**Verdict:** Comments are a red herring. The real issue is tracked changes in the MAIN document causing text differences between `.text` and `_build_visible_text_map()`.

---

## Impact Analysis

### Before Fix:
- 11 obvious changes suggested by LLM
- 0 successfully applied (0% success rate)
- All marked as CONTEXT_AMBIGUOUS
- User frustrated: "to a human the changes would be obvious"

### After Fix (Expected):
- Same 11 changes
- 9-11 successfully applied (82-100% success rate)
- Context matching works correctly
- Remaining failures (if any) due to legitimate ambiguity, not extraction mismatch

---

## Summary

**Problem:** Two different text extraction methods produce incompatible results
**Root Cause:** `paragraph.text` vs `_build_visible_text_map()` inconsistency
**Solution:** Use `_build_visible_text_map()` in both extraction and application
**Effort:** Minimal (1 line change, a few hours of testing)
**Impact:** High (fixes critical real-world failure case)
**Priority:** Urgent (blocks practical usage of fallback document feature)
