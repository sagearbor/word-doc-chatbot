# Sequential Edit Bug Fix: Approach 2 - Specific Text Priority

## Problem Statement

The current Word document processing system fails to apply sequential edits correctly because it requires **full contextual_old_text match** even when the `specific_old_text` still exists in the document after previous changes.

### Root Cause

In `replace_text_in_paragraph_with_tracked_change()` (lines 576-766), the matching logic follows this sequence:

1. **First**: Find `contextual_old_text` in paragraph (lines 605-617)
2. **Then**: Find `specific_old_text` within that context (lines 623-642)

**Problem**: If Edit #1 modifies part of Edit #2's context, the full `contextual_old_text` no longer exists, causing Edit #2 to fail with `CONTEXT_NOT_FOUND` even though `specific_old_text` is still present and unchanged.

### Example Failure Scenario

**Original text**: "The cost is $100 and the fee is $50."

**Edit #1**: Change "$100" to "$150" (within context "cost is $100 and")
- ✅ Success: Context found, specific text found

**Edit #2**: Change "$50" to "$75" (within context "$100 and the fee is $50")
- ❌ Failure: Context now reads "$150 and the fee is $50" (doesn't match "$100 and the fee is $50")
- 🔴 **Bug**: "$50" is still present and could be changed, but system never tries because context check fails first

## Proposed Solution: Specific Text Priority

### Core Strategy

**Reverse the matching priority**: Search for `specific_old_text` **FIRST**, use `contextual_old_text` **ONLY** for disambiguation when multiple matches exist.

### New Logic Flow

```python
# 1. Find ALL occurrences of specific_old_text in paragraph
occurrences = find_all_occurrences(specific_old_text, paragraph_text)

if len(occurrences) == 0:
    # Specific text not found - try fuzzy matching
    fuzzy_match = fuzzy_search_best_match(specific_old_text, paragraph_text)
    if fuzzy_match:
        return apply_edit_at_position(fuzzy_match)
    else:
        return SPECIFIC_TEXT_NOT_FOUND

elif len(occurrences) == 1:
    # Unique match - apply immediately without context check
    return apply_edit_at_position(occurrences[0])

else:  # len(occurrences) > 1
    # Multiple matches - use context to disambiguate
    best_match = find_occurrence_near_context(occurrences, contextual_old_text)
    if best_match:
        return apply_edit_at_position(best_match)
    else:
        # Context didn't help - mark all occurrences with orange highlight
        return AMBIGUOUS_MULTIPLE_MATCHES
```

## Implementation Details

### Function to Modify

**`replace_text_in_paragraph_with_tracked_change()`** in `backend/word_processor.py` (lines 576-766)

### Required Changes

#### 1. Find All Specific Text Occurrences

```python
def find_all_specific_text_occurrences(
    specific_text: str,
    paragraph_text: str,
    case_sensitive: bool
) -> List[Dict[str, int]]:
    """
    Find all occurrences of specific_text in paragraph_text.

    Returns:
        List of dicts with 'start' and 'end' positions for each match
    """
    search_text = paragraph_text if case_sensitive else paragraph_text.lower()
    search_target = specific_text if case_sensitive else specific_text.lower()

    occurrences = []
    try:
        for match in re.finditer(re.escape(search_target), search_text):
            occurrences.append({
                "start": match.start(),
                "end": match.end(),
                "text": paragraph_text[match.start():match.end()]
            })
    except re.error as e:
        # Handle regex errors
        return []

    return occurrences
```

#### 2. Disambiguation Algorithm (Multiple Matches)

```python
def find_best_match_using_context(
    occurrences: List[Dict[str, int]],
    contextual_old_text: str,
    paragraph_text: str,
    case_sensitive: bool
) -> Optional[Dict[str, int]]:
    """
    When multiple specific_text matches exist, use context to pick the best one.

    Strategy:
    1. Check if any occurrence's surrounding text matches contextual_old_text exactly
    2. If not, use fuzzy matching to find the occurrence with best context match
    3. Return the occurrence with highest context similarity score

    Args:
        occurrences: List of specific_text match positions
        contextual_old_text: The full context string from LLM
        paragraph_text: The full paragraph text
        case_sensitive: Whether to use case-sensitive matching

    Returns:
        Best matching occurrence dict, or None if no good match found
    """
    search_para = paragraph_text if case_sensitive else paragraph_text.lower()
    search_context = contextual_old_text if case_sensitive else contextual_old_text.lower()

    best_match = None
    best_score = 0.0

    for occurrence in occurrences:
        # Extract surrounding context for this occurrence
        # Use a window of ±100 characters (or length of contextual_old_text, whichever is larger)
        window_size = max(100, len(contextual_old_text))

        start_window = max(0, occurrence['start'] - window_size)
        end_window = min(len(paragraph_text), occurrence['end'] + window_size)

        surrounding_text = paragraph_text[start_window:end_window]
        search_surrounding = surrounding_text if case_sensitive else surrounding_text.lower()

        # Method 1: Exact context match
        if search_context in search_surrounding:
            # Found exact context match - this is the winner
            return occurrence

        # Method 2: Fuzzy context match
        # Calculate similarity between contextual_old_text and surrounding text
        similarity = SequenceMatcher(None, search_context, search_surrounding).ratio()

        if similarity > best_score:
            best_score = similarity
            best_match = occurrence

    # Return best match if similarity is above threshold (e.g., 0.7)
    if best_score >= 0.7:
        return best_match

    return None
```

#### 3. Updated Main Logic

Replace lines 605-642 with:

```python
# NEW APPROACH: Find specific_old_text FIRST
log_debug(f"P{current_para_idx+1}: Searching for specific_old_text: '{specific_old_text_llm}'")

specific_occurrences = find_all_specific_text_occurrences(
    specific_old_text_llm,
    visible_paragraph_text_original_case,
    case_sensitive_flag
)

if len(specific_occurrences) == 0:
    # No exact match - try fuzzy matching
    log_debug(f"P{current_para_idx+1}: Specific text '{specific_old_text_llm}' not found. Trying fuzzy match...")

    fuzzy_match = fuzzy_search_best_match(
        specific_old_text_llm if case_sensitive_flag else specific_old_text_llm.lower(),
        search_text_in_doc
    )

    if fuzzy_match and fuzzy_match['similarity'] >= FUZZY_MATCHING_THRESHOLD:
        # Found fuzzy match - use it
        global_specific_start_offset = fuzzy_match['start']
        global_specific_end_offset = fuzzy_match['end']
        actual_specific_old_text_to_delete = fuzzy_match['matched_text']
        fuzzy_match_used = True
        fuzzy_similarity = fuzzy_match['similarity']

        log_debug(f"P{current_para_idx+1}: Fuzzy match found: '{actual_specific_old_text_to_delete}' "
                  f"(similarity: {fuzzy_similarity:.2f})")
    else:
        # No match found (exact or fuzzy)
        log_debug(f"P{current_para_idx+1}: Specific text '{specific_old_text_llm}' NOT FOUND "
                  f"(exact or fuzzy). Change skipped.")
        ambiguous_or_failed_changes_log.append({
            "paragraph_index": current_para_idx,
            "issue": "Specific text not found in paragraph (tried exact and fuzzy matching).",
            **edit_details_for_log
        })
        return "SPECIFIC_TEXT_NOT_FOUND", None

elif len(specific_occurrences) == 1:
    # UNIQUE MATCH - Apply immediately without context check
    unique_occurrence = specific_occurrences[0]
    global_specific_start_offset = unique_occurrence['start']
    global_specific_end_offset = unique_occurrence['end']
    actual_specific_old_text_to_delete = unique_occurrence['text']
    fuzzy_match_used = False
    fuzzy_similarity = 1.0

    log_debug(f"P{current_para_idx+1}: Unique specific text match found at "
              f"{global_specific_start_offset}-{global_specific_end_offset}. "
              f"Applying change WITHOUT context validation.")

    # Skip context check entirely - proceed directly to boundary validation

else:  # len(specific_occurrences) > 1
    # MULTIPLE MATCHES - Use context to disambiguate
    log_debug(f"P{current_para_idx+1}: Found {len(specific_occurrences)} occurrences of "
              f"'{specific_old_text_llm}'. Using context to disambiguate...")

    best_match = find_best_match_using_context(
        specific_occurrences,
        contextual_old_text_llm,
        visible_paragraph_text_original_case,
        case_sensitive_flag
    )

    if best_match:
        # Found best match using context
        global_specific_start_offset = best_match['start']
        global_specific_end_offset = best_match['end']
        actual_specific_old_text_to_delete = best_match['text']
        fuzzy_match_used = False
        fuzzy_similarity = 1.0

        log_debug(f"P{current_para_idx+1}: Disambiguated using context. Selected match at "
                  f"{global_specific_start_offset}-{global_specific_end_offset}")
    else:
        # Context didn't help - can't disambiguate
        log_debug(f"P{current_para_idx+1}: Multiple matches found but context-based disambiguation failed. "
                  f"Marking as ambiguous.")

        # Return ambiguous status with all occurrences for orange highlighting
        return "CONTEXT_AMBIGUOUS", specific_occurrences

# Continue with boundary validation and XML manipulation
# (existing code from line 651 onwards remains the same)
```

### Key Advantages of This Approach

1. **Sequential Edits Work**: Edit #2 succeeds even if Edit #1 changed part of its context
2. **Context Still Useful**: Context disambiguates when specific_old_text appears multiple times
3. **Minimal False Negatives**: As long as specific_old_text exists unchanged, edit can proceed
4. **Backward Compatible**: Still uses context when needed, just not as a strict requirement

## Edge Cases Handled

### Edge Case 1: Specific Text Appears Once
**Scenario**: "The price is $100."
**Edit**: Change "$100" to "$150"
**Result**: ✅ Applied immediately (unique match, no context check needed)

### Edge Case 2: Specific Text Appears Multiple Times, Context Helps
**Scenario**: "The price is $100 and the discount is $100."
**Edit**: Change first "$100" to "$150" (context: "price is $100 and")
**Result**: ✅ Context disambiguates to select first "$100"

### Edge Case 3: Specific Text Appears Multiple Times, Context Doesn't Help
**Scenario**: "The price is $100 and the discount is $100."
**Edit**: Change "$100" to "$150" (context: "value is $100") ← context doesn't exist
**Result**: 🟧 Both "$100" instances highlighted orange for manual review

### Edge Case 4: Sequential Edits with Context Overlap
**Scenario**: "The cost is $100 and the fee is $50."
**Edit #1**: Change "$100" to "$150"
**After Edit #1**: "The cost is $150 and the fee is $50."
**Edit #2**: Change "$50" to "$75" (original context: "$100 and the fee is $50")
**Result**:
- **Current System**: ❌ Fails with CONTEXT_NOT_FOUND
- **Specific Priority**: ✅ Succeeds (finds "$50", which is unique, applies change)

### Edge Case 5: Specific Text Changed by Prior Edit
**Scenario**: "The price is $100."
**Edit #1**: Change "$100" to "$150"
**After Edit #1**: "The price is $150."
**Edit #2**: Change "$100" to "$200"
**Result**:
- ✅ Correctly returns SPECIFIC_TEXT_NOT_FOUND (text no longer exists)
- Avoids false positive (Edit #2 is obsolete)

### Edge Case 6: Partial Context Match After Prior Edit
**Scenario**: "The old price was $100 and the new price is $200."
**Edit #1**: Change "$100" to "$150"
**After Edit #1**: "The old price was $150 and the new price is $200."
**Edit #2**: Change "$200" to "$250" (context: "old price was $100 and the new price is $200")
**Result**:
- **Current System**: ❌ Fails (context "$100 and the new price is $200" doesn't match)
- **Specific Priority**: ✅ Succeeds (finds unique "$200", applies change)

### Edge Case 7: Fuzzy Match Needed Due to Prior Edit
**Scenario**: "The price is $100.00 for members."
**Edit #1**: Change "members" to "registered members"
**After Edit #1**: "The price is $100.00 for registered members."
**Edit #2**: Change "$100.00" to "$125.00" (LLM might have slight spacing difference: "$100. 00")
**Result**:
- **Specific Priority with Fuzzy**: ✅ Fuzzy matching finds "$100.00" even with minor variations
- Threshold (0.85) ensures high-confidence matches only

## Boundary Validation Remains Important

Even with specific text priority, boundary validation (lines 651-669) remains critical:

```python
# Ensure specific_old_text is word-bounded
char_before = paragraph_text[start - 1] if start > 0 else None
char_after = paragraph_text[end] if end < len(paragraph_text) else None

is_start_ok = (start == 0 or (char_before and char_before.isspace()))
is_end_ok = (end == len(paragraph_text) or
             (char_after and (char_after.isspace() or
                              char_after in ALLOWED_POST_BOUNDARY_PUNCTUATION)))

if not (is_start_ok and is_end_ok):
    return "SKIPPED_INVALID_BOUNDARY", None
```

**Why**: Prevents false matches like "$1" matching "$100" or "the" matching "there".

## Testing Strategy

### Test Case 1: Basic Sequential Edits
```python
original_text = "The price is $100 and the fee is $50."
edits = [
    {
        "contextual_old_text": "price is $100 and",
        "specific_old_text": "$100",
        "specific_new_text": "$150",
        "reason_for_change": "Update price"
    },
    {
        "contextual_old_text": "$100 and the fee is $50",  # Context will be outdated after Edit #1
        "specific_old_text": "$50",
        "specific_new_text": "$75",
        "reason_for_change": "Update fee"
    }
]
expected_result = "The price is $150 and the fee is $75."
```

**Expected Behavior**:
- Edit #1: ✅ Applied (context matches, unique "$100")
- Edit #2: ✅ Applied (context doesn't match, but unique "$50" found anyway)

### Test Case 2: Multiple Occurrences with Context Disambiguation
```python
original_text = "The first value is $100 and the second value is $100."
edits = [
    {
        "contextual_old_text": "first value is $100 and",
        "specific_old_text": "$100",
        "specific_new_text": "$150",
        "reason_for_change": "Update first value"
    }
]
expected_result = "The first value is $150 and the second value is $100."
```

**Expected Behavior**:
- Edit #1: ✅ Applied to first "$100" only (context disambiguates)
- Second "$100": ✅ Unchanged (correct)

### Test Case 3: Three Sequential Edits with Context Cascade
```python
original_text = "The base cost is $100, the tax is $10, and the total is $110."
edits = [
    {
        "contextual_old_text": "base cost is $100, the",
        "specific_old_text": "$100",
        "specific_new_text": "$200",
        "reason_for_change": "Double the base cost"
    },
    {
        "contextual_old_text": "cost is $100, the tax is $10",  # Context outdated after Edit #1
        "specific_old_text": "$10",
        "specific_new_text": "$20",
        "reason_for_change": "Double the tax"
    },
    {
        "contextual_old_text": "tax is $10, and the total is $110",  # Context outdated after Edit #2
        "specific_old_text": "$110",
        "specific_new_text": "$220",
        "reason_for_change": "Update total"
    }
]
expected_result = "The base cost is $200, the tax is $20, and the total is $220."
```

**Expected Behavior**:
- Edit #1: ✅ Applied (unique "$100")
- Edit #2: ✅ Applied (unique "$10", despite outdated context)
- Edit #3: ✅ Applied (unique "$110", despite outdated context)

### Test Case 4: Ambiguous Match Requires Context
```python
original_text = "The discount is $50 and the rebate is $50."
edits = [
    {
        "contextual_old_text": "discount is $50 and",
        "specific_old_text": "$50",
        "specific_new_text": "$75",
        "reason_for_change": "Increase discount"
    }
]
expected_result = "The discount is $75 and the rebate is $50."
```

**Expected Behavior**:
- Edit #1: ✅ Applied to first "$50" (context disambiguates)
- Second "$50": ✅ Unchanged

### Test Case 5: Context Can't Disambiguate
```python
original_text = "The price is $50 and the cost is $50."
edits = [
    {
        "contextual_old_text": "value is $50",  # This context doesn't exist
        "specific_old_text": "$50",
        "specific_new_text": "$75",
        "reason_for_change": "Update value"
    }
]
expected_result = "Both '$50' instances highlighted orange (ambiguous)"
```

**Expected Behavior**:
- Edit #1: 🟧 Ambiguous (2 occurrences, context doesn't match either)
- Orange highlighting applied to both for manual review

## Performance Considerations

### Time Complexity

**Current Approach**:
- Context search: O(n × m) where n = paragraph length, m = context length
- Specific search within context: O(c × s) where c = context length, s = specific length
- **Total**: O(n×m + c×s)

**Specific Priority Approach**:
- Find all specific occurrences: O(n × s)
- Context disambiguation (if needed): O(k × n × m) where k = number of occurrences
- **Total**: O(n×s + k×n×m)

**Analysis**:
- **Best case** (unique specific match): Specific Priority is **faster** (skips context search)
- **Worst case** (many occurrences): Slightly slower, but acceptable (k is usually small: 2-5)
- **Sequential edits**: Specific Priority is **significantly faster** (avoids CONTEXT_NOT_FOUND failures)

### Memory Usage

Both approaches have similar memory footprint:
- Store paragraph text: O(n)
- Store edit details: O(e) where e = number of edits
- Store occurrences list: O(k) where k = matches found

**Difference**: Specific Priority temporarily stores all occurrences (small overhead).

## Migration Path

### Phase 1: Add New Functions (Non-Breaking)
1. Implement `find_all_specific_text_occurrences()`
2. Implement `find_best_match_using_context()`
3. Add unit tests for new functions

### Phase 2: Update Main Logic with Feature Flag
```python
USE_SPECIFIC_TEXT_PRIORITY = True  # Global flag

def replace_text_in_paragraph_with_tracked_change(...):
    if USE_SPECIFIC_TEXT_PRIORITY:
        # New logic (specific text priority)
        ...
    else:
        # Old logic (context priority)
        ...
```

### Phase 3: A/B Testing
- Run both approaches on test suite
- Compare success rates and performance
- Validate that new approach doesn't break existing functionality

### Phase 4: Full Deployment
- Set `USE_SPECIFIC_TEXT_PRIORITY = True` permanently
- Remove old code path
- Update documentation

## Comparison with Approach 1 (Context Interpolation)

| Aspect | Approach 1: Context Interpolation | Approach 2: Specific Text Priority |
|--------|-----------------------------------|-------------------------------------|
| **Core Strategy** | Update context after each edit | Prioritize specific_old_text search |
| **Complexity** | High (track edit effects, update contexts) | Low (just reorder search priority) |
| **Code Changes** | Large (major refactoring) | Small (localized to one function) |
| **Risk** | High (complex state management) | Low (minimal changes) |
| **Sequential Edits** | ✅ Works perfectly | ✅ Works perfectly |
| **Context Preservation** | ✅ Always uses context | ⚠️ Context optional (only for disambiguation) |
| **Performance** | ⚠️ O(n²) context updates | ✅ O(n) with minimal overhead |
| **Ambiguity Handling** | ✅ Context always valid | ✅ Context used for disambiguation |
| **False Positives** | Low | Low (boundary checks prevent) |
| **Testing Burden** | High (complex state tracking) | Low (straightforward logic) |

## Recommendation

**Implement Approach 2: Specific Text Priority**

**Rationale**:
1. **Simpler Implementation**: Changes localized to one function
2. **Lower Risk**: Minimal code changes, easier to test
3. **Better Performance**: Faster for sequential edits (skips unnecessary context checks)
4. **Sufficient Solution**: Solves the sequential edit bug without over-engineering
5. **Backward Compatible**: Still uses context when needed for disambiguation

**When Approach 1 Would Be Better**:
- If context validation is **critically important** for compliance/auditing
- If false positives (wrong instance of specific_old_text) are **unacceptable**
- If performance is not a concern and complexity is acceptable

For most use cases, **Approach 2 provides the best balance of simplicity, performance, and correctness**.

## Implementation Checklist

- [ ] Create `find_all_specific_text_occurrences()` function
- [ ] Create `find_best_match_using_context()` function
- [ ] Add `USE_SPECIFIC_TEXT_PRIORITY` global flag
- [ ] Update `replace_text_in_paragraph_with_tracked_change()` logic (lines 605-642)
- [ ] Add logging for new code paths
- [ ] Write unit tests for new functions
- [ ] Create integration tests for sequential edits
- [ ] Run full test suite (golden dataset)
- [ ] A/B test both approaches on real-world documents
- [ ] Update CLAUDE.md documentation
- [ ] Create user-facing release notes

## Status

**PROPOSED - NOT YET IMPLEMENTED**

This document describes the proposed solution. Implementation requires code changes to `backend/word_processor.py`.
