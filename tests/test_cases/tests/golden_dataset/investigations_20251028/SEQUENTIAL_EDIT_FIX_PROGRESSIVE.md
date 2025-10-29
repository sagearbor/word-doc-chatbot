# Sequential Edit Fix: Progressive Fallback Strategy (Approach 3)

## Problem Statement

When applying sequential edits to a Word document, earlier edits modify the paragraph text, causing later edits with the same `contextual_old_text` to fail with `CONTEXT_NOT_FOUND`. The current implementation performs exact string matching and stops immediately when the contextual text cannot be found.

### Example Failure Scenario

**Initial paragraph text:**
```
"The patient was diagnosed with diabetes. Treatment includes insulin therapy."
```

**Two sequential edits:**
1. **Edit 1**: Change "diabetes" → "type 2 diabetes"
   - `contextual_old_text`: "diagnosed with diabetes. Treatment"
   - `specific_old_text`: "diabetes"
   - `specific_new_text`: "type 2 diabetes"
   - **Result**: SUCCESS

2. **Edit 2**: Change "insulin therapy" → "insulin and metformin therapy"
   - `contextual_old_text`: "diagnosed with diabetes. Treatment includes insulin therapy"
   - `specific_old_text`: "insulin therapy"
   - `specific_new_text`: "insulin and metformin therapy"
   - **Result**: CONTEXT_NOT_FOUND (because text now says "type 2 diabetes")

---

## Solution: Progressive Fallback Strategy

Implement a **multi-level fallback cascade** that tries increasingly lenient matching strategies, moving from strictest (exact match) to most flexible (anywhere in paragraph), while logging which level was used for transparency and audit purposes.

### Design Philosophy

1. **Safety First**: Start with exact matching to prevent false positives
2. **Progressive Flexibility**: Only relax constraints when safer methods fail
3. **Transparency**: Log which matching level was used for each edit
4. **Bounded Flexibility**: Set clear limits on how lenient matching can become

---

## Implementation Design

### Multi-Level Matching Strategy

The progressive fallback implements **4 levels** of matching, each progressively more lenient:

#### **Level 1: Exact Contextual Match (Current Behavior)**
- **Strategy**: Find exact `contextual_old_text` in paragraph
- **Safety**: Highest - no ambiguity
- **When it works**: When paragraph text hasn't been modified by prior edits
- **When it fails**: After sequential edits change the context

```python
# Level 1: Exact context match
search_context = contextual_old_text.lower() if not case_sensitive else contextual_old_text
if search_context in paragraph_text:
    # Find specific_old_text within the matched context
    return find_exact_position(contextual_old_text, specific_old_text, paragraph_text)
```

**Example**:
- Looking for: `"diagnosed with diabetes. Treatment"`
- In paragraph: `"The patient was diagnosed with diabetes. Treatment includes..."`
- **Match**: Exact match found at position 17-52

---

#### **Level 2: Partial Context Match (Edge Word Removal)**
- **Strategy**: Remove words from edges of `contextual_old_text` to handle minor modifications
- **Safety**: High - still requires substantial context overlap
- **When it works**: When edits modified words at the boundaries of the context
- **Implementation**: Try removing 1-5 words from start/end of context

```python
# Level 2: Partial context match (try removing edge words)
context_words = contextual_old_text.split()
max_words_to_remove = min(5, len(context_words) // 3)  # Remove up to 1/3 or 5 words

for words_to_remove in range(1, max_words_to_remove + 1):
    # Try removing from end
    partial_context_end = ' '.join(context_words[:-words_to_remove])
    if partial_context_end in paragraph_text:
        position = find_position_near_context(partial_context_end, specific_old_text, paragraph_text)
        if position:
            log_debug(f"Level 2 match: Removed {words_to_remove} words from end")
            return position

    # Try removing from start
    partial_context_start = ' '.join(context_words[words_to_remove:])
    if partial_context_start in paragraph_text:
        position = find_position_near_context(partial_context_start, specific_old_text, paragraph_text)
        if position:
            log_debug(f"Level 2 match: Removed {words_to_remove} words from start")
            return position

    # Try removing from both sides
    if words_to_remove < len(context_words) // 2:
        partial_context_both = ' '.join(context_words[words_to_remove:-words_to_remove])
        if partial_context_both in paragraph_text:
            position = find_position_near_context(partial_context_both, specific_old_text, paragraph_text)
            if position:
                log_debug(f"Level 2 match: Removed {words_to_remove} words from both sides")
                return position
```

**Example**:
- Original context: `"diagnosed with diabetes. Treatment includes insulin"`
- After Edit 1: `"diagnosed with type 2 diabetes. Treatment includes insulin"`
- Level 2 tries:
  - Remove 1 word from end: `"diagnosed with diabetes. Treatment includes"` → No match
  - Remove 2 words from end: `"diagnosed with diabetes. Treatment"` → No match
  - Remove 1 word from start: `"with diabetes. Treatment includes insulin"` → Match!
- **Success**: Found specific_old_text within reduced context

---

#### **Level 3: Specific Text with Proximity Check**
- **Strategy**: Find `specific_old_text` in paragraph, verify it's near expected location
- **Safety**: Medium - uses paragraph position and surrounding context for validation
- **When it works**: When context is heavily modified but target text is intact
- **Proximity validation**: Ensure match is within reasonable distance of expected location

```python
# Level 3: Specific text with proximity check
# Use paragraph index and estimated position to validate
def find_with_proximity_check(specific_old_text, paragraph_text, expected_position_ratio):
    """
    Find specific_old_text and verify it's near where we expect it to be.

    Args:
        specific_old_text: The text to find
        paragraph_text: The full paragraph text
        expected_position_ratio: Where in paragraph we expect it (0.0-1.0)

    Returns:
        Position info if found within proximity threshold, None otherwise
    """
    search_text = specific_old_text.lower() if not case_sensitive else specific_old_text
    paragraph_search = paragraph_text.lower() if not case_sensitive else paragraph_text

    # Find all occurrences
    occurrences = []
    start = 0
    while True:
        pos = paragraph_search.find(search_text, start)
        if pos == -1:
            break
        occurrences.append(pos)
        start = pos + 1

    if not occurrences:
        return None

    # If only one occurrence, use it (high confidence)
    if len(occurrences) == 1:
        log_debug(f"Level 3 match: Single occurrence of '{specific_old_text}'")
        return {"start": occurrences[0], "end": occurrences[0] + len(specific_old_text)}

    # Multiple occurrences - choose closest to expected position
    expected_pos = int(len(paragraph_text) * expected_position_ratio)
    closest_match = min(occurrences, key=lambda pos: abs(pos - expected_pos))
    distance = abs(closest_match - expected_pos)

    # Accept if within 200 characters of expected position
    if distance <= 200:
        log_debug(f"Level 3 match: Closest match at {closest_match} (expected ~{expected_pos}, distance: {distance})")
        return {"start": closest_match, "end": closest_match + len(specific_old_text)}
    else:
        log_debug(f"Level 3 failed: Closest match too far (distance: {distance} > 200 chars)")
        return None
```

**Example**:
- Context heavily modified: `"diagnosed with type 2 diabetes mellitus. Treatment regimen includes insulin"`
- Looking for: `"insulin therapy"`
- Level 3: Finds "insulin" at expected position (near end of sentence)
- **Success**: Proximity validated, change applied

---

#### **Level 4: Specific Text Anywhere (Last Resort)**
- **Strategy**: Find `specific_old_text` anywhere in paragraph
- **Safety**: Lowest - high risk of false positives
- **When it works**: As absolute fallback when all else fails
- **Logging**: Always logs a **WARNING** when this level is used

```python
# Level 4: Specific text anywhere in paragraph (LAST RESORT)
search_text = specific_old_text.lower() if not case_sensitive else specific_old_text
paragraph_search = paragraph_text.lower() if not case_sensitive else paragraph_text

if search_text in paragraph_search:
    pos = paragraph_search.find(search_text)
    log_message = (
        f"WARNING: P{para_idx+1}: Using LEVEL 4 FALLBACK (last resort) - "
        f"specific text '{specific_old_text}' found without context validation. "
        f"This may be a false positive. Manual review recommended."
    )
    print(log_message)
    ambiguous_or_failed_changes_log.append({
        "paragraph_index": para_idx,
        "issue": "Level 4 fallback used - context not found, matched specific text only",
        "type": "Warning",
        **edit_details_for_log
    })
    return {"start": pos, "end": pos + len(specific_old_text)}
else:
    # Absolutely no match found
    return None
```

**Example**:
- Context completely rewritten
- Looking for: `"insulin therapy"`
- Level 4: Finds "insulin therapy" at position 85
- **Warning logged**: Manual review recommended

---

## Implementation Function

### Core Function: `find_text_with_progressive_fallback()`

```python
def find_text_with_progressive_fallback(
    paragraph_text: str,
    contextual_old_text: str,
    specific_old_text: str,
    case_sensitive: bool,
    para_idx: int,
    edit_details_for_log: Dict,
    ambiguous_or_failed_changes_log: List[Dict]
) -> Optional[Dict]:
    """
    Find specific_old_text in paragraph_text using progressive fallback strategy.

    Args:
        paragraph_text: Current paragraph text to search in
        contextual_old_text: The broader context from LLM
        specific_old_text: The specific text to find and replace
        case_sensitive: Whether search is case-sensitive
        para_idx: Paragraph index for logging
        edit_details_for_log: Edit details for logging
        ambiguous_or_failed_changes_log: Log list to append warnings/errors

    Returns:
        Dict with 'start', 'end', 'matched_text', 'level' or None if not found
    """
    search_context = contextual_old_text if case_sensitive else contextual_old_text.lower()
    search_paragraph = paragraph_text if case_sensitive else paragraph_text.lower()
    search_specific = specific_old_text if case_sensitive else specific_old_text.lower()

    # LEVEL 1: Exact contextual match
    if search_context in search_paragraph:
        ctx_start = search_paragraph.find(search_context)
        actual_context = paragraph_text[ctx_start:ctx_start + len(contextual_old_text)]

        # Find specific within context
        if search_specific in (actual_context if case_sensitive else actual_context.lower()):
            spec_start_in_ctx = (actual_context if case_sensitive else actual_context.lower()).find(search_specific)
            global_start = ctx_start + spec_start_in_ctx
            global_end = global_start + len(specific_old_text)
            matched_text = paragraph_text[global_start:global_end]

            log_debug(f"P{para_idx+1}: Level 1 (exact context) match for '{specific_old_text}'")
            return {
                'start': global_start,
                'end': global_end,
                'matched_text': matched_text,
                'level': 1
            }

    # LEVEL 2: Partial context match (remove edge words)
    context_words = contextual_old_text.split()
    max_words_to_remove = min(5, max(1, len(context_words) // 3))

    for num_words in range(1, max_words_to_remove + 1):
        # Try removing from end
        if num_words < len(context_words):
            partial_end = ' '.join(context_words[:-num_words])
            result = _try_partial_context_match(
                paragraph_text, partial_end, specific_old_text,
                case_sensitive, para_idx, f"end ({num_words} words)"
            )
            if result:
                result['level'] = 2
                return result

        # Try removing from start
        if num_words < len(context_words):
            partial_start = ' '.join(context_words[num_words:])
            result = _try_partial_context_match(
                paragraph_text, partial_start, specific_old_text,
                case_sensitive, para_idx, f"start ({num_words} words)"
            )
            if result:
                result['level'] = 2
                return result

        # Try removing from both sides
        if num_words * 2 < len(context_words):
            partial_both = ' '.join(context_words[num_words:-num_words])
            result = _try_partial_context_match(
                paragraph_text, partial_both, specific_old_text,
                case_sensitive, para_idx, f"both sides ({num_words} words each)"
            )
            if result:
                result['level'] = 2
                return result

    # LEVEL 3: Specific text with proximity check
    # Estimate where in paragraph we expect the text based on context position
    expected_ratio = 0.5  # Default to middle if we can't estimate
    if contextual_old_text:
        # Rough estimate: where would context start in original paragraph?
        # Use first/last few words to guess position
        first_words = ' '.join(contextual_old_text.split()[:3])
        last_words = ' '.join(contextual_old_text.split()[-3:])

        # Try to find either start or end markers
        search_first = first_words if case_sensitive else first_words.lower()
        search_last = last_words if case_sensitive else last_words.lower()

        if search_first in search_paragraph:
            marker_pos = search_paragraph.find(search_first)
            expected_ratio = marker_pos / len(paragraph_text)
        elif search_last in search_paragraph:
            marker_pos = search_paragraph.find(search_last)
            expected_ratio = marker_pos / len(paragraph_text)

    result = _find_with_proximity_check(
        paragraph_text, specific_old_text, expected_ratio,
        case_sensitive, para_idx
    )
    if result:
        result['level'] = 3
        log_debug(f"P{para_idx+1}: Level 3 (proximity check) match for '{specific_old_text}'")
        ambiguous_or_failed_changes_log.append({
            "paragraph_index": para_idx,
            "issue": f"Level 3 fallback used - found '{specific_old_text}' via proximity check",
            "type": "Info",
            **edit_details_for_log
        })
        return result

    # LEVEL 4: Specific text anywhere (LAST RESORT)
    if search_specific in search_paragraph:
        pos = search_paragraph.find(search_specific)
        matched_text = paragraph_text[pos:pos + len(specific_old_text)]

        log_message = (
            f"WARNING: P{para_idx+1}: Level 4 (LAST RESORT) - "
            f"found '{specific_old_text}' without context validation at position {pos}. "
            f"Manual review recommended."
        )
        print(log_message)
        ambiguous_or_failed_changes_log.append({
            "paragraph_index": para_idx,
            "issue": "Level 4 fallback used - context completely lost, matched specific text only",
            "type": "Warning",
            **edit_details_for_log
        })

        return {
            'start': pos,
            'end': pos + len(specific_old_text),
            'matched_text': matched_text,
            'level': 4
        }

    # No match at any level
    log_debug(f"P{para_idx+1}: No match found at any level for '{specific_old_text}'")
    return None


def _try_partial_context_match(
    paragraph_text: str,
    partial_context: str,
    specific_old_text: str,
    case_sensitive: bool,
    para_idx: int,
    removal_description: str
) -> Optional[Dict]:
    """Helper function to try matching with partial context."""
    search_partial = partial_context if case_sensitive else partial_context.lower()
    search_paragraph = paragraph_text if case_sensitive else paragraph_text.lower()
    search_specific = specific_old_text if case_sensitive else specific_old_text.lower()

    if search_partial in search_paragraph:
        ctx_start = search_paragraph.find(search_partial)
        actual_context = paragraph_text[ctx_start:ctx_start + len(partial_context)]

        if search_specific in (actual_context if case_sensitive else actual_context.lower()):
            spec_start_in_ctx = (actual_context if case_sensitive else actual_context.lower()).find(search_specific)
            global_start = ctx_start + spec_start_in_ctx
            global_end = global_start + len(specific_old_text)
            matched_text = paragraph_text[global_start:global_end]

            log_debug(f"P{para_idx+1}: Level 2 match (removed from {removal_description}) for '{specific_old_text}'")
            return {
                'start': global_start,
                'end': global_end,
                'matched_text': matched_text
            }

    return None


def _find_with_proximity_check(
    paragraph_text: str,
    specific_old_text: str,
    expected_position_ratio: float,
    case_sensitive: bool,
    para_idx: int
) -> Optional[Dict]:
    """Helper function to find text with proximity validation."""
    search_specific = specific_old_text if case_sensitive else specific_old_text.lower()
    search_paragraph = paragraph_text if case_sensitive else paragraph_text.lower()

    # Find all occurrences
    occurrences = []
    start_pos = 0
    while True:
        pos = search_paragraph.find(search_specific, start_pos)
        if pos == -1:
            break
        occurrences.append(pos)
        start_pos = pos + 1

    if not occurrences:
        return None

    # Single occurrence - high confidence
    if len(occurrences) == 1:
        matched_text = paragraph_text[occurrences[0]:occurrences[0] + len(specific_old_text)]
        return {
            'start': occurrences[0],
            'end': occurrences[0] + len(specific_old_text),
            'matched_text': matched_text
        }

    # Multiple occurrences - use proximity
    expected_pos = int(len(paragraph_text) * expected_position_ratio)
    closest_match = min(occurrences, key=lambda pos: abs(pos - expected_pos))
    distance = abs(closest_match - expected_pos)

    # Accept within 200 character threshold
    if distance <= 200:
        matched_text = paragraph_text[closest_match:closest_match + len(specific_old_text)]
        log_debug(f"P{para_idx+1}: Proximity match - closest occurrence at {closest_match} (expected ~{expected_pos}, distance: {distance})")
        return {
            'start': closest_match,
            'end': closest_match + len(specific_old_text),
            'matched_text': matched_text
        }

    return None
```

---

## Integration with Existing Code

### Modify `replace_text_in_paragraph_with_tracked_change()`

Replace the current exact matching logic (lines 605-642 in word_processor.py) with the progressive fallback:

```python
def replace_text_in_paragraph_with_tracked_change(
        doc, current_para_idx: int, paragraph,
        contextual_old_text_llm, specific_old_text_llm, specific_new_text,
        reason_for_change, author, case_sensitive_flag,
        ambiguous_or_failed_changes_log) -> Tuple[str, Optional[List[Dict[str, Any]]]]:

    # ... (existing initialization code) ...

    # NEW: Use progressive fallback instead of exact matching
    match_result = find_text_with_progressive_fallback(
        paragraph_text=visible_paragraph_text_original_case,
        contextual_old_text=contextual_old_text_llm,
        specific_old_text=specific_old_text_llm,
        case_sensitive=case_sensitive_flag,
        para_idx=current_para_idx,
        edit_details_for_log=edit_details_for_log,
        ambiguous_or_failed_changes_log=ambiguous_or_failed_changes_log
    )

    if not match_result:
        log_debug(f"P{current_para_idx+1}: No match found at any fallback level for '{specific_old_text_llm}'")
        return "CONTEXT_NOT_FOUND", None

    # Extract match information
    global_specific_start_offset = match_result['start']
    global_specific_end_offset = match_result['end']
    actual_specific_old_text_to_delete = match_result['matched_text']
    match_level = match_result['level']

    log_debug(f"P{current_para_idx+1}: Match found at Level {match_level} for '{specific_old_text_llm}'")
    log_debug(f"P{current_para_idx+1}: Global offsets: {global_specific_start_offset}-{global_specific_end_offset}")

    # ... (continue with existing boundary checking and XML manipulation) ...
```

---

## Logging and Transparency

### Logging Output Examples

**Level 1 (Exact Match)**:
```
DEBUG (word_processor): P3: Level 1 (exact context) match for 'insulin therapy'
SUCCESS: P3: Applied change for context 'Treatment includes insulin therapy...', specific 'insulin therapy'.
```

**Level 2 (Partial Context)**:
```
DEBUG (word_processor): P3: Level 2 match (removed from end (2 words)) for 'insulin therapy'
SUCCESS: P3: Applied change using Level 2 fallback for 'insulin therapy'.
```

**Level 3 (Proximity Check)**:
```
DEBUG (word_processor): P3: Proximity match - closest occurrence at 85 (expected ~80, distance: 5)
DEBUG (word_processor): P3: Level 3 (proximity check) match for 'insulin therapy'
INFO: P3: Level 3 fallback used - found 'insulin therapy' via proximity check
SUCCESS: P3: Applied change using Level 3 fallback for 'insulin therapy'.
```

**Level 4 (Last Resort)**:
```
WARNING: P3: Level 4 (LAST RESORT) - found 'insulin therapy' without context validation at position 85. Manual review recommended.
SUCCESS: P3: Applied change using Level 4 fallback for 'insulin therapy'. MANUAL REVIEW RECOMMENDED.
```

---

## Advantages

### 1. **Handles Sequential Edits**
- Later edits can find their target text even after context is modified
- Graceful degradation from strict to flexible matching

### 2. **Maintains Safety**
- Always tries exact matching first (current behavior)
- Only uses flexible matching as fallback
- Boundary checking still applies at all levels

### 3. **Transparency**
- Every match level is logged
- Users can see when fallbacks were used
- Level 4 triggers explicit warnings

### 4. **No False Negatives**
- Reduces "CONTEXT_NOT_FOUND" failures
- Improves success rate for sequential edits

### 5. **Configurable**
- Can adjust thresholds (proximity distance, max words to remove)
- Can disable certain levels if too risky
- Can tune logging verbosity

---

## Disadvantages

### 1. **Increased Complexity**
- More code paths to test
- More edge cases to handle
- Harder to debug when something goes wrong

### 2. **Potential False Positives (Level 4)**
- Last resort matching could apply edits to wrong text
- Requires manual review when Level 4 is used

### 3. **Performance Impact**
- Multiple matching attempts per edit
- Could slow down processing for documents with many edits

### 4. **Ambiguity Risk**
- Level 3/4 might match wrong occurrence in paragraphs with repeated text
- Proximity heuristics may not always be accurate

---

## Risk Mitigation

### Preventing False Positives

1. **Boundary Validation Still Required**
   - All levels must pass boundary checking
   - Ensures matches are word-bounded

2. **Logging for Audit**
   - All Level 3/4 matches are logged
   - Users can review which edits used fallback

3. **Optional Level Disabling**
   - Add configuration to disable Level 4 if too risky
   - Add flag to limit to Level 2 only

```python
# Configuration flags
ENABLE_LEVEL_3_FALLBACK = True  # Proximity matching
ENABLE_LEVEL_4_FALLBACK = False  # Disable last resort by default
```

4. **Statistics Reporting**
   - Track how many edits used each level
   - Report in log file summary

```python
# In process_document_with_edits()
level_counts = {1: 0, 2: 0, 3: 0, 4: 0}

# After processing
print(f"\nMatch Level Statistics:")
print(f"  Level 1 (Exact Context): {level_counts[1]} edits")
print(f"  Level 2 (Partial Context): {level_counts[2]} edits")
print(f"  Level 3 (Proximity Check): {level_counts[3]} edits")
print(f"  Level 4 (Last Resort): {level_counts[4]} edits")
if level_counts[4] > 0:
    print(f"  WARNING: {level_counts[4]} edits used Level 4 - manual review recommended!")
```

---

## Testing Strategy

### Test Cases to Implement

1. **Level 1 Tests** (Exact Match - should work as current code):
   - Single edit with exact context
   - Multiple edits with unique contexts

2. **Level 2 Tests** (Partial Context):
   - Two edits where first edit modifies end of second edit's context
   - Two edits where first edit modifies start of second edit's context
   - Edge case: Context reduced to very few words

3. **Level 3 Tests** (Proximity):
   - Context completely rewritten but specific text intact
   - Multiple occurrences of specific text, proximity selects correct one
   - Edge case: Specific text moved significantly from expected position

4. **Level 4 Tests** (Last Resort):
   - Context unrecognizable, only specific text remains
   - Verify warning is logged
   - Edge case: Multiple identical specific texts (should prefer first)

5. **Regression Tests**:
   - Ensure existing test cases still pass
   - Verify no false positives introduced

### Example Test

```python
def test_progressive_fallback_level_2():
    """Test that Level 2 handles sequential edits that modify context edges."""
    doc = Document()
    para = doc.add_paragraph("The patient was diagnosed with diabetes. Treatment includes insulin therapy.")

    edits = [
        {
            "contextual_old_text": "diagnosed with diabetes. Treatment",
            "specific_old_text": "diabetes",
            "specific_new_text": "type 2 diabetes",
            "reason_for_change": "Specify diabetes type"
        },
        {
            # Context now says "type 2 diabetes" but edit still has "diabetes"
            "contextual_old_text": "diagnosed with diabetes. Treatment includes insulin therapy",
            "specific_old_text": "insulin therapy",
            "specific_new_text": "insulin and metformin therapy",
            "reason_for_change": "Add metformin to treatment"
        }
    ]

    success, log_file, logs, count = process_document_with_edits(
        input_path, output_path, edits, debug_mode_flag=True
    )

    assert success, "Processing should succeed"
    assert count == 2, "Both edits should be applied"

    # Check that second edit used Level 2
    level_2_used = any(
        "Level 2" in log.get("issue", "")
        for log in logs
        if log.get("type") == "Info"
    )
    assert level_2_used, "Second edit should use Level 2 fallback"

    # Verify final text
    final_text = doc.paragraphs[0].text
    assert "type 2 diabetes" in final_text
    assert "insulin and metformin therapy" in final_text
```

---

## Configuration Options

### Recommended Configuration Flags

Add to top of `word_processor.py`:

```python
# --- Progressive Fallback Configuration ---
ENABLE_PROGRESSIVE_FALLBACK = True  # Master switch
ENABLE_LEVEL_2_FALLBACK = True  # Partial context matching
ENABLE_LEVEL_3_FALLBACK = True  # Proximity-based matching
ENABLE_LEVEL_4_FALLBACK = False  # Last resort (disabled by default for safety)

# Level 2 Configuration
MAX_WORDS_TO_REMOVE = 5  # Maximum words to strip from context edges
MIN_CONTEXT_WORDS = 3  # Minimum context words required after removal

# Level 3 Configuration
PROXIMITY_THRESHOLD_CHARS = 200  # Maximum distance from expected position
PROXIMITY_ACCEPT_SINGLE_OCCURRENCE = True  # Auto-accept if only one match

# Logging
LOG_FALLBACK_LEVEL_USAGE = True  # Log which level was used for each match
WARN_ON_LEVEL_4_USAGE = True  # Print warning when Level 4 is used
```

---

## Migration Plan

### Phase 1: Implementation
1. Implement `find_text_with_progressive_fallback()` function
2. Implement helper functions (`_try_partial_context_match`, `_find_with_proximity_check`)
3. Add configuration flags

### Phase 2: Integration
1. Modify `replace_text_in_paragraph_with_tracked_change()` to call progressive fallback
2. Add match level to success logging
3. Add level statistics tracking

### Phase 3: Testing
1. Run existing test suite (ensure no regressions)
2. Add new test cases for each level
3. Test on golden dataset documents

### Phase 4: Monitoring
1. Deploy with Level 4 disabled
2. Monitor Level 3 usage and false positive rate
3. Collect user feedback on warnings

---

## Recommendations

### For Production Use

1. **Start Conservative**:
   - Enable Levels 1-3 only
   - Disable Level 4 until proven necessary
   - Monitor Level 3 warning logs

2. **Tune Thresholds**:
   - Adjust `MAX_WORDS_TO_REMOVE` based on typical edit patterns
   - Adjust `PROXIMITY_THRESHOLD_CHARS` based on average paragraph length

3. **User Communication**:
   - Document that Level 3+ matches need review
   - Provide clear warnings in UI when fallbacks are used
   - Add "Match Confidence" indicator in processing logs

4. **Fallback to Manual Review**:
   - When Level 4 would be used, optionally skip edit and flag for manual review
   - Add "manual review queue" feature in UI

---

## Comparison with Other Approaches

| Aspect | **Approach 3 (Progressive Fallback)** | Approach 1 (State Tracking) | Approach 2 (Dynamic Context) |
|--------|-------------------------------------|----------------------------|----------------------------|
| **Complexity** | Medium (4 matching levels) | High (track all edits) | Very High (regenerate context) |
| **LLM Dependency** | None | None | High (LLM call per failed edit) |
| **Performance** | Fast (local matching) | Fast (state lookups) | Slow (LLM calls) |
| **Accuracy** | Good (bounded flexibility) | Excellent (perfect tracking) | Excellent (LLM understands context) |
| **False Positives** | Low-Medium (Level 4 risk) | Very Low | Very Low |
| **Transparency** | Excellent (logged levels) | Good (state tracking) | Good (LLM reasoning) |
| **Edge Cases** | Handles most | Handles all | Handles all |
| **Implementation Risk** | Low (incremental fallback) | Medium (state complexity) | High (LLM reliability) |

---

## Conclusion

The Progressive Fallback Strategy provides a **balanced approach** to handling sequential edits:

- **Maintains current safety** for unchanged paragraphs (Level 1)
- **Adds flexibility** for modified contexts (Levels 2-3)
- **Provides escape hatch** for edge cases (Level 4)
- **Transparent logging** for audit and debugging

**Recommended for production** with Level 4 disabled initially, monitoring Level 3 usage to tune thresholds.

---

## Example Output Log

```
--- LOG OF CHANGES NOT MADE, AMBIGUITIES, OR WARNINGS (2025-10-28 14:32:15) ---
Input DOCX: legal_document_v1.docx
Output DOCX: legal_document_v1_processed.docx
Total Edit Instructions Provided: 15
Edits Successfully Applied This Run: 15
Log Items (Failures/Warnings/Errors/Info): 3

Match Level Statistics:
  Level 1 (Exact Context): 12 edits (80%)
  Level 2 (Partial Context): 2 edits (13%)
  Level 3 (Proximity Check): 1 edit (7%)
  Level 4 (Last Resort): 0 edits (0%)

-----------------------------------------
Paragraph Index (1-based): 3
Original Visible Text Snippet: The patient was diagnosed with type 2 diabetes. Treatment includes insulin and metformin therapy.
LLM Context Searched: 'diagnosed with diabetes. Treatment includes insulin therapy'
LLM Specific Old Text: 'insulin therapy'
LLM Specific New Text: 'insulin and metformin therapy'
LLM Reason for Change: 'Add metformin to treatment regimen'
Issue/Status: Level 2 fallback used - found 'insulin therapy' with partial context (removed 1 word from start)
Log Entry Type: Info
-----------------------------------------
```

---

**File Location**: `/dcri/sasusers/home/scb2/gitRepos/word-doc-chatbot/SEQUENTIAL_EDIT_FIX_PROGRESSIVE.md`

**Status**: Ready for implementation review and testing
