# Hypothesis 2: Next Steps - Gradual Complexity Testing

**Status:** Ready for implementation
**Goal:** Find the optimal prompt complexity that gets correct output without timeouts

## Quick Answer

**What did we learn?**
- ✅ Simple prompt (1,200 chars) = LLM responds but wrong format
- ❌ Complex prompt (2,700 chars) = Timeout, no response
- 🎯 Need middle ground: Enough detail for correct format, not so much it times out

**What to do next?**
Test prompts with increasing complexity until we find the breaking point.

## Incremental Test Plan

### Test 1: Simple Baseline (COMPLETED)
**Status:** ✅ Done
**Prompt length:** ~1,200 characters
**Result:** Gets response, wrong format (0/6 edits applied)

### Test 2: Add Format Specification
**Status:** ⏳ Next to implement
**Add to prompt:**
```
For each requirement, convert to a "Change X to Y" instruction:
- Find text in the main document that matches the requirement
- Specify what old text to replace
- Provide the new text

Format: "1. Change 'old text phrase' to 'new text phrase'"
```
**Expected length:** ~1,500 characters
**Expected outcome:** Correct format, but may lack specificity

### Test 3: Add One Concrete Example
**Status:** ⏳ After Test 2
**Add to prompt:**
```
Example:
Requirement: "The contractor must complete work within 30 days"
Main document text: "work should be completed in a reasonable timeframe"
Correct instruction: "1. Change 'work should be completed in a reasonable timeframe' to 'work must be completed within 30 business days of project start'"
```
**Expected length:** ~1,700 characters
**Expected outcome:** Better text matching, higher success rate

### Test 4: Add Text Finding Rules
**Status:** ⏳ After Test 3
**Add to prompt:**
```
IMPORTANT:
- Look ONLY in the main document for text to modify
- DO NOT look for fallback document text in main document
- Use exact text from main document (at least 10-15 words)
- For missing requirements: Find the closest related text to enhance
```
**Expected length:** ~1,900 characters
**Expected outcome:** More accurate text matching

### Test 5: Add Insertion Instructions
**Status:** ⏳ After Test 4
**Add to prompt:**
```
For NEW REQUIREMENTS (not found in main document):
Format: "In the [Section Name] section, after the text 'exact anchor text', ADD: 'new requirement text'"

Example: "In the DELIVERABLES section, after 'Quality standards will be maintained.', ADD: 'All work must meet industry best practices.'"
```
**Expected length:** ~2,100 characters
**Expected outcome:** Handles both replacements and insertions

### Test 6: Complexity Threshold Test
**Status:** ⏳ After Test 5
**Gradually add:** More examples, more rules, more formatting details
**Goal:** Find the exact character count where timeouts start occurring

## Implementation Script

Create a test script that automatically runs all levels:

```python
# tests/test_incremental_prompt_complexity.py

PROMPT_LEVELS = {
    "level_1_simple": {
        "length": 1200,
        "adds": "Simple request only",
        "template": "Read this fallback document and extract all requirements as numbered instructions..."
    },
    "level_2_format": {
        "length": 1500,
        "adds": "Format specification",
        "template": "Read this fallback document...\n\nFor each requirement, convert to 'Change X to Y' format..."
    },
    "level_3_example": {
        "length": 1700,
        "adds": "One concrete example",
        "template": "Read this fallback document...\n\nFor each requirement...\n\nExample: Requirement: 'contractor must complete work within 30 days'..."
    },
    # ... etc
}

def test_prompt_level(level_name, prompt_template):
    """Test a specific prompt complexity level"""
    # Call endpoint with this prompt
    # Measure: response time, success rate, format correctness
    # Return metrics
    pass

def run_incremental_test_suite():
    """Run all prompt levels and identify optimal complexity"""
    results = {}
    for level, config in PROMPT_LEVELS.items():
        print(f"Testing {level}: {config['adds']}")
        metrics = test_prompt_level(level, config['template'])
        results[level] = metrics

        # Stop if we hit timeout
        if metrics['timeout']:
            print(f"❌ Timeout at {level} ({config['length']} chars)")
            break

        # Stop if we get 100% success
        if metrics['success_rate'] == 1.0:
            print(f"✅ Optimal level found: {level}")
            break

    return results
```

## Quick Implementation (For Next Session)

**File to modify:** `backend/legal_document_processor.py`
**Function:** `extract_conditional_instructions_with_llm()`

**Simple approach for Test 2:**

```python
# Test 2: Add format specification
prompt = f"""Read this fallback document and extract all requirements as numbered instructions.

Fallback document (first 1000 chars):
{content_preview}

For each requirement, convert to a "Change X to Y" instruction:
- Find related text in the main document
- Specify what old text to replace
- Provide the new text

Format: "1. Change 'old text phrase' to 'new text phrase'"

Return only numbered instructions, nothing else."""
```

**Expected improvement:** Instructions in correct format, but may not match exact text.

## Success Criteria

For each test level, measure:

1. **Response Rate:** Did LLM respond without timeout? (Target: 100%)
2. **Format Correctness:** Are instructions in "Change X to Y" format? (Target: 100%)
3. **Text Matching:** Do instructions reference actual main document text? (Target: > 70%)
4. **Application Success:** What % of edits were successfully applied? (Target: > 80%)
5. **Response Time:** How long did LLM take to respond? (Target: < 30 seconds)

**Stop when:**
- Success rate drops below 50% (too simple)
- Timeouts occur consistently (too complex)
- Sweet spot found: 80%+ success rate, < 30 sec response time

## Expected Findings

**Hypothesis:**
- Level 1 (simple): 0-20% success rate
- Level 2 (+ format): 30-50% success rate
- Level 3 (+ example): 60-70% success rate
- Level 4 (+ rules): 80-90% success rate
- Level 5 (+ insertions): 90-95% success rate
- Level 6 (full complex): Timeout or 95-100% success rate

**Optimal level:** Likely Level 3 or 4 (1,700-1,900 characters)

## Files to Create

1. `/tests/test_incremental_prompt_complexity.py` - Automated test runner
2. `/tests/prompt_templates/` - Directory with each prompt level template
3. `/tests/results/incremental_complexity_results.json` - Test results

## Time Estimate

- **Test 2 implementation:** 10 minutes
- **Test 2 run + analysis:** 5 minutes
- **Full incremental suite:** 30-45 minutes total
- **Analysis and optimization:** 15 minutes

**Total:** ~1 hour to find optimal prompt complexity

## Decision Point

After completing these tests, you will know:

1. **Optimal prompt length** (in characters)
2. **Required prompt elements** (format, examples, rules)
3. **Maximum complexity before timeout**
4. **Expected success rate at optimal level**

This will allow you to **confidently modify the production prompt** with evidence-based changes.

## Related Documents

- [HYPOTHESIS_2_RESULTS.md](./HYPOTHESIS_2_RESULTS.md) - Test 1 results
- [COMPLETE_CASE_02_ANALYSIS.md](./COMPLETE_CASE_02_ANALYSIS.md) - Original diagnosis
- [DEBUG_PLAN_CASE_02_COMPLEX.md](./DEBUG_PLAN_CASE_02_COMPLEX.md) - Debug plan

## Questions for User

1. **Priority:** Should we continue with incremental testing now, or is this analysis sufficient?
2. **Scope:** Test only case_02, or run full test suite at each level?
3. **Automation:** Create automated test suite, or manually test each level?
4. **Threshold:** What success rate is acceptable? (80%? 90%? 95%?)
