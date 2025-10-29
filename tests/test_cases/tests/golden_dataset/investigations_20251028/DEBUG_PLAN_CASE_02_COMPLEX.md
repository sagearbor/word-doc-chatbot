# Debug Plan: Case 02 Complex Fallback (0 Edits Generated)

## Problem Statement
**Simplified fallback works** (4 edits), but **complex fallback returns 0 edits**.

## Root Cause Evidence
From `/tmp/backend_logs.txt`:
- Line 27: LLM called with comprehensive fallback document
- Line 30: `❌ LLM returned empty conditional analysis`
- The LLM IS being called correctly, but returns empty response

**This is a "flavor of null" problem** - the LLM might be:
1. Returning actual empty string
2. Returning whitespace that gets stripped
3. Returning error message that's not being logged
4. Timing out and returning nothing
5. Returning malformed response that's being rejected

## Hypotheses to Test (in parallel)

### Hypothesis 1: LLM Response Not Captured
**Theory**: The LLM returns something, but it's being lost in parsing
**Test**: Add raw response logging before any parsing
**File**: `backend/legal_document_processor.py:extract_conditional_instructions_with_llm()`
**Fix**: Log the complete raw response object from LiteLLM

### Hypothesis 2: Exception Not Being Caught
**Theory**: LLM call throws exception that's being silently caught
**Test**: Add try/except with detailed exception logging
**File**: `backend/legal_document_processor.py:extract_conditional_instructions_with_llm()`
**Fix**: Wrap LLM call in try/except and log full traceback

### Hypothesis 3: Prompt Too Long/Complex
**Theory**: Complex fallback document exceeds token limits or confuses LLM
**Test**: Simplify the prompt while keeping the same fallback document
**File**: `backend/legal_document_processor.py:extract_conditional_instructions_with_llm()`
**Fix**: Create shorter, more directive prompt

### Hypothesis 4: LLM Correctly Returns Empty with Reason
**Theory**: LLM intentionally returns empty because it doesn't understand task
**Test**: Ask LLM to ALWAYS return explanation, even if no instructions found
**File**: `backend/legal_document_processor.py:extract_conditional_instructions_with_llm()`
**Fix**: Modify prompt to say "If you find no instructions, explain WHY in detail"

### Hypothesis 5: Azure OpenAI Model Limitation
**Theory**: gpt-5-mini doesn't handle this complex task well
**Test**: Try with different model (gpt-4) for this specific call
**File**: `backend/legal_document_processor.py:extract_conditional_instructions_with_llm()`
**Fix**: Override model selection for this specific LLM call

### Hypothesis 6: Response Format Issue
**Theory**: LLM returns valid response but in unexpected format
**Test**: Remove response_format constraint and parse flexibly
**File**: `backend/legal_document_processor.py:extract_conditional_instructions_with_llm()`
**Fix**: Don't force JSON, accept any text response

### Hypothesis 7: Fallback Document Content Issue
**Theory**: The comprehensive fallback has formatting that breaks extraction
**Test**: Read the actual fallback document and see if it has issues
**File**: `tests/test_cases/case_02_contract_editing/fallback/case_02_fallback_comprehensive_guidelines.docx`
**Fix**: Verify fallback content is readable

## Testing Strategy

### Phase 1: Diagnostic Logging (Tech-Lead-Developer Agent #1)
- Add comprehensive logging to `extract_conditional_instructions_with_llm()`
- Log raw LLM response before any processing
- Log any exceptions with full stack traces
- Test with complex fallback and capture all logs

### Phase 2: Prompt Simplification (Tech-Lead-Developer Agent #2)
- Create much simpler prompt that still asks for analysis instructions
- Test if simpler prompt gets response
- If yes, incrementally add complexity to find breaking point

### Phase 3: Force Response (Tech-Lead-Developer Agent #3)
- Modify prompt to REQUIRE explanation even if empty
- Add "If no instructions, respond with: 'NO_INSTRUCTIONS_FOUND: <reason>'"
- Test and log what LLM actually returns

### Phase 4: Model Upgrade Test (Tech-Lead-Developer Agent #4)
- Temporarily override to use GPT-4 for this specific call
- Test if more powerful model handles complex fallback
- If yes, we know it's model capability issue

### Phase 5: Fallback Content Analysis (Tech-Lead-Developer Agent #5)
- Read the comprehensive fallback DOCX directly
- Check for any XML corruption, weird formatting, or unreadable sections
- Compare with simplified fallback that works

## Success Criteria

**Minimum**: Understand WHY the LLM returns empty (not just fix it)
**Good**: Get LLM to generate at least some instructions from complex fallback
**Best**: Generate all 9 expected instructions from complex fallback

## Regression Prevention

### Test Case Matrix
Create 4 versions of case_02:
1. **case_02a_simple** - Direct text replacements (already exists as SIMPLIFIED)
2. **case_02b_moderate** - Mix of replacements + 2-3 abstract requirements
3. **case_02c_complex** - Current comprehensive guidelines (9 abstract requirements)
4. **case_02d_extreme** - 15+ abstract requirements of various types

All must pass after fixes to ensure we don't break anything.

## Implementation Plan

1. ✅ Create this debug plan
2. Launch 5 tech-lead-developer agents in parallel (one per hypothesis)
3. Each agent tests their hypothesis and reports findings
4. Synthesize findings and implement best fix
5. Test against all 4 case_02 variants
6. Update documentation

## Notes

- DO NOT simplify the complex fallback - users will use odd inputs
- DO NOT reduce functionality of simplified fallback to fix complex
- Focus on making the LLM robust to handle both cases
- The session memory file has excellent details on sequential edit issue too
