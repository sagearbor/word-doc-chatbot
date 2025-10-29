# Sequential Edit Fix: Fuzzy Matching Flow Diagram

## Current Behavior (Bug)

```
┌─────────────────────────────────────────────────────────────┐
│ Original Paragraph:                                         │
│ "The project deadline is November 15, 2024. Contact Smith."│
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ EDIT #1:                                                    │
│ Context: "deadline is November 15, 2024"                   │
│ Old: "November 15" → New: "December 1"                     │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼ SUCCESS
┌─────────────────────────────────────────────────────────────┐
│ Modified Paragraph:                                         │
│ "The project deadline is December 1, 2024. Contact Smith." │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ EDIT #2:                                                    │
│ Context: "deadline is November 15, 2024. Contact Smith"    │
│                     ^^^^^^^^^ (NO LONGER EXISTS!)           │
│ Old: "Smith" → New: "Johnson"                              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼ EXACT MATCH FAILS
┌─────────────────────────────────────────────────────────────┐
│ Status: CONTEXT_NOT_FOUND ❌                                │
│ Result: Edit #2 SKIPPED                                     │
└─────────────────────────────────────────────────────────────┘
```

## Fixed Behavior (Fuzzy Matching)

```
┌─────────────────────────────────────────────────────────────┐
│ Original Paragraph:                                         │
│ "The project deadline is November 15, 2024. Contact Smith."│
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ EDIT #1:                                                    │
│ Context: "deadline is November 15, 2024"                   │
│ Old: "November 15" → New: "December 1"                     │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼ SUCCESS (Exact Match)
┌─────────────────────────────────────────────────────────────┐
│ Modified Paragraph:                                         │
│ "The project deadline is December 1, 2024. Contact Smith." │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ EDIT #2:                                                    │
│ Context: "deadline is November 15, 2024. Contact Smith"    │
│ Old: "Smith" → New: "Johnson"                              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼ TIER 1: EXACT MATCH
┌─────────────────────────────────────────────────────────────┐
│ Searching for:                                              │
│   "deadline is November 15, 2024. Contact Smith"           │
│ In paragraph:                                               │
│   "The project deadline is December 1, 2024. Contact Smith"│
│                                                             │
│ Result: NO EXACT MATCH ❌                                   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼ TIER 2: FUZZY FALLBACK
┌─────────────────────────────────────────────────────────────┐
│ fuzzy_search_best_match()                                   │
│                                                             │
│ Target:  "deadline is November 15, 2024. Contact Smith"    │
│           ^^^^^^^^^^^^^^^^^^^^       ^^^^^^^^^^^^^^        │
│           (unchanged portions)                              │
│                                                             │
│ Candidate: "deadline is December 1, 2024. Contact Smith"   │
│                                                             │
│ Similarity Calculation:                                     │
│   - Total chars: 47                                         │
│   - Changed: "November 15" → "December 1" (7 chars)        │
│   - Similarity: ~87% ✓ (threshold: 85%)                    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼ FUZZY MATCH FOUND
┌─────────────────────────────────────────────────────────────┐
│ Match Info:                                                 │
│   - Start: 16                                               │
│   - End: 63                                                 │
│   - Matched: "deadline is December 1, 2024. Contact Smith" │
│   - Similarity: 87%                                         │
│   - Method: "fuzzy"                                         │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼ FIND SPECIFIC TEXT
┌─────────────────────────────────────────────────────────────┐
│ Searching for "Smith" within matched context...            │
│ Found at position 57-62 ✓                                   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼ SUCCESS (Fuzzy Context Match)
┌─────────────────────────────────────────────────────────────┐
│ Final Paragraph:                                            │
│ "The project deadline is December 1, 2024. Contact Johnson"│
│                                                             │
│ Log Output:                                                 │
│   SUCCESS: P1: Applied edit #1 (exact match)               │
│   FUZZY_CONTEXT_MATCH: P1: Context matched at 87%          │
│   SUCCESS (FUZZY 87%): P1: Applied edit #2                 │
└─────────────────────────────────────────────────────────────┘
```

## Two-Tier Matching Algorithm Flow

```
                    ┌─────────────────────┐
                    │ Start Edit Process  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Get paragraph text  │
                    │ Get context to find │
                    └──────────┬──────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
                ▼                             ▼
    ┌────────────────────────┐   ┌────────────────────────┐
    │   TIER 1: EXACT MATCH  │   │  CASE SENSITIVITY?     │
    │   re.finditer()        │   │  Apply .lower() if     │
    │   O(n) - Fast          │   │  case-insensitive      │
    └──────────┬─────────────┘   └────────────┬───────────┘
               │                              │
               └──────────────┬───────────────┘
                              │
                              ▼
               ┌──────────────────────────┐
               │ Exact match found?       │
               └──────────┬───────────────┘
                          │
                ┌─────────┴─────────┐
                │                   │
              YES                  NO
                │                   │
                ▼                   ▼
    ┌────────────────────┐  ┌──────────────────────┐
    │ Return match list  │  │ Fuzzy matching       │
    │ with similarity    │  │ enabled?             │
    │ = 1.0 (100%)       │  └──────┬───────────────┘
    └─────────┬──────────┘         │
              │              ┌─────┴──────┐
              │             YES            NO
              │              │             │
              │              ▼             ▼
              │  ┌─────────────────────┐  │
              │  │ TIER 2: FUZZY MATCH │  │
              │  │ fuzzy_search_best_  │  │
              │  │ match()             │  │
              │  │ O(n*m) - Slower     │  │
              │  └──────────┬──────────┘  │
              │             │              │
              │             ▼              │
              │  ┌─────────────────────┐  │
              │  │ Similarity ≥ 85%?   │  │
              │  └──────────┬──────────┘  │
              │             │              │
              │       ┌─────┴─────┐        │
              │      YES           NO      │
              │       │            │       │
              │       ▼            └───────┼──────┐
              │  ┌─────────────────────┐  │      │
              │  │ Return fuzzy match  │  │      │
              │  │ with similarity     │  │      │
              │  │ score (e.g., 87%)   │  │      │
              │  └──────────┬──────────┘  │      │
              │             │              │      │
              └─────────────┼──────────────┘      │
                            │                     │
                            ▼                     ▼
              ┌──────────────────────────────────────┐
              │ How many matches found?              │
              └──────────────┬───────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
          0 matches      1 match      2+ matches
              │              │              │
              ▼              ▼              ▼
    ┌─────────────────┐ ┌────────────┐ ┌──────────────────┐
    │ CONTEXT_NOT_    │ │ Find       │ │ CONTEXT_         │
    │ FOUND           │ │ specific   │ │ AMBIGUOUS        │
    │                 │ │ text in    │ │                  │
    │ Edit skipped ❌ │ │ context    │ │ Orange highlight │
    └─────────────────┘ │            │ │ all occurrences  │
                        └──────┬─────┘ └──────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Apply tracked       │
                    │ change with XML     │
                    │ manipulation        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ SUCCESS ✓           │
                    │ (exact or fuzzy)    │
                    └─────────────────────┘
```

## Similarity Threshold Visualization

```
Similarity Scale (0% to 100%)
═══════════════════════════════════════════════════════════

0%  ┌───────────────────────────────────────────────────┐
    │ Completely different text                         │
    │ "The quick brown fox" vs "Lorem ipsum dolor sit"  │
    └───────────────────────────────────────────────────┘

50% ┌───────────────────────────────────────────────────┐
    │ Partially similar                                 │
    │ "The project deadline November 15" vs            │
    │ "The assignment due date December 1"              │
    └───────────────────────────────────────────────────┘

75% ┌───────────────────────────────────────────────────┐
    │ Mostly similar (aggressive threshold)             │
    │ "The project deadline is November 15" vs          │
    │ "The project deadline is December 1"              │
    │ (~78% similarity - would NOT match at 85%)        │
    └───────────────────────────────────────────────────┘

85% ┌═══════════════════════════════════════════════════┐ ◄── THRESHOLD
    ║ CURRENT THRESHOLD (Recommended)                   ║
    ║ Balanced: Handles reasonable changes              ║
    ║ Example: 1-2 words changed in 10-word context     ║
    └═══════════════════════════════════════════════════┘

90% ┌───────────────────────────────────────────────────┐
    │ Very similar (conservative threshold)             │
    │ Minor changes only                                │
    │ "The project deadline is Nov 15" vs               │
    │ "The project deadline is Nov 16"                  │
    └───────────────────────────────────────────────────┘

95% ┌───────────────────────────────────────────────────┐
    │ Nearly identical                                  │
    │ 1 character change in 20+ chars                   │
    └───────────────────────────────────────────────────┘

100%┌───────────────────────────────────────────────────┐
    │ Exact match (no fuzzy matching needed)           │
    │ Uses Tier 1 exact match (faster)                 │
    └───────────────────────────────────────────────────┘
```

## Example Similarity Calculations

### Example 1: Single Word Change (87% similarity)
```
Original Context (Edit #1 state):
"deadline is November 15, 2024. Contact Smith"
                                        ^^^^^

Modified Context (After Edit #1):
"deadline is December 1, 2024. Contact Smith"
             ^^^^^^^^^^

Calculation:
- Total characters: 47
- Matching characters: ~41
- Similarity: 41/47 ≈ 87.2% ✓ PASSES (≥ 85%)
```

### Example 2: Multiple Word Changes (76% similarity)
```
Original Context:
"The project deadline is November 15, 2024"

Modified Context:
"The assignment due date is December 1, 2024"
    ^^^^^^^^^^  ^^^^^^^^

Calculation:
- Total characters: 42
- Changed: "project deadline" → "assignment due date" (10 chars)
- Similarity: ~76% ✗ FAILS (< 85%)
```

### Example 3: Punctuation Change (96% similarity)
```
Original Context:
"Contact Dr. Smith for questions."

Modified Context:
"Contact Dr. Jones for questions."
            ^^^^^

Calculation:
- Total characters: 32
- Changed: "Smith" → "Jones" (1 char diff position)
- Similarity: ~96.8% ✓ PASSES (≥ 85%)
```

## Performance Comparison

```
┌─────────────────────────────────────────────────────────────┐
│ Performance Characteristics                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ TIER 1: Exact Match (regex)                                │
│   Time Complexity: O(n) where n = paragraph length         │
│   Typical Time: 0.05 - 0.2 ms per edit                     │
│   Used For: 80-95% of edits (unchanged paragraphs)         │
│                                                             │
│ TIER 2: Fuzzy Match (sliding window)                       │
│   Time Complexity: O(n*m) where m = context length         │
│   Typical Time: 2 - 10 ms per edit                         │
│   Used For: 5-20% of edits (modified paragraphs)           │
│                                                             │
│ Impact on 500-paragraph document with 50 edits:            │
│   - 40 exact matches: 40 × 0.1ms = 4ms                     │
│   - 10 fuzzy matches: 10 × 5ms = 50ms                      │
│   - Total: ~54ms (negligible overhead)                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Edge Case Handling Matrix

```
┌───────────────────────┬───────────────┬─────────────────────┐
│ Edge Case             │ Detection     │ Handling            │
├───────────────────────┼───────────────┼─────────────────────┤
│ 2+ fuzzy matches      │ len(matches)  │ CONTEXT_AMBIGUOUS   │
│ found above threshold │ > 1           │ Orange highlight    │
├───────────────────────┼───────────────┼─────────────────────┤
│ Context too short     │ len(context)  │ Skip fuzzy matching │
│ (< 3 chars)           │ < 3           │ Use exact only      │
├───────────────────────┼───────────────┼─────────────────────┤
│ Specific text not in  │ ValueError    │ Try fuzzy match for │
│ fuzzy-matched context │ on .index()   │ specific text too   │
├───────────────────────┼───────────────┼─────────────────────┤
│ Similarity exactly at │ similarity    │ PASSES (inclusive)  │
│ 85% threshold         │ == 0.85       │ threshold check     │
├───────────────────────┼───────────────┼─────────────────────┤
│ Case-insensitive mode │ Check flag    │ Apply .lower() to   │
│                       │               │ both strings first  │
├───────────────────────┼───────────────┼─────────────────────┤
│ Fuzzy matching        │ Check global  │ Use exact match     │
│ disabled              │ flag          │ only (fallback off) │
└───────────────────────┴───────────────┴─────────────────────┘
```

## Code Location Map

```
backend/word_processor.py
│
├── Lines 22-23: Configuration
│   ├── FUZZY_MATCHING_ENABLED = True
│   └── FUZZY_MATCHING_THRESHOLD = 0.85
│
├── Lines 62-137: Fuzzy Matching Functions (EXISTING)
│   ├── fuzzy_search_best_match()        ← Reused for context
│   ├── fuzzy_find_text_in_context()     ← Already used for specific text
│   └── is_boundary_valid_fuzzy()        ← Boundary validation
│
├── Lines 576-766: Main Edit Function
│   │
│   ├── Lines 605-614: Context Matching (MODIFY HERE)
│   │   ├── [TIER 1] Exact regex match
│   │   └── [TIER 2] Fuzzy fallback ← ADD THIS
│   │
│   ├── Lines 625-642: Specific Text Matching (EXISTING)
│   │   ├── Exact match try/except
│   │   └── Fuzzy fallback ← Already implemented
│   │
│   └── Lines 842-845: Success Logging (ENHANCE)
│       └── Add fuzzy match indicator
│
└── Lines 897-903: Status Handling (NO CHANGE)
    └── CONTEXT_NOT_FOUND handling
```

## Expected Log Output Examples

### Before Fix (Bug):
```
DEBUG: P1: Attempting in P1: Context='deadline is November 15...', SpecificOld='November 15'
SUCCESS: P1: Applied change for context 'deadline is November 15...', specific 'November 15'.
DEBUG: P1: Attempting in P1: Context='deadline is November 15...', SpecificOld='Smith'
DEBUG: P1: LLM Context 'deadline is November 15...' not found in paragraph text.
INFO: P1: Edit skipped - CONTEXT_NOT_FOUND for 'Smith'
```

### After Fix (Working):
```
DEBUG: P1: Attempting in P1: Context='deadline is November 15...', SpecificOld='November 15'
SUCCESS: P1: Applied change for context 'deadline is November 15...', specific 'November 15'.
DEBUG: P1: Attempting in P1: Context='deadline is November 15...', SpecificOld='Smith'
DEBUG: P1: LLM Context 'deadline is November 15...' not found in paragraph text.
DEBUG: P1: Exact context match failed. Attempting fuzzy match with threshold 0.85...
DEBUG: P1: Fuzzy context match found with 87.23% similarity at 16-63
FUZZY_CONTEXT_MATCH: P1: Matched context with 87% similarity (threshold: 85%)
SUCCESS (FUZZY 87%): P1: Applied change for context 'deadline is November 15...', specific 'Smith'.
```
