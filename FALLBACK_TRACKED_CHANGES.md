# Fallback Document with Tracked Changes Feature

## Overview

The fallback document feature now supports two modes of operation:

1. **Tracked Changes Mode** (NEW): Upload a fallback document that contains tracked changes, and those changes will be automatically extracted and applied to the main document
2. **Requirements Mode** (Existing): Upload a fallback document with requirements text, and AI will interpret and generate appropriate edits

## How It Works

### Tracked Changes Mode (Preferred)

**When to use:** You have a reference document with tracked changes showing the edits you want to apply

**Process:**
1. Upload your main document (the document to be edited)
2. Upload a fallback document that contains tracked changes
3. The system automatically detects tracked changes in the fallback document
4. Tracked changes are extracted as structured data:
   - Insertions (new text added)
   - Deletions (text removed)
   - Substitutions (text replaced)
5. These changes are directly applied to the main document as new tracked changes
6. No LLM processing needed - faster and more accurate!

**Example Use Case:**
```
Main Document: Contract_v1.docx (original contract)
Fallback Document: Contract_v1_with_edits.docx (same contract with tracked changes from legal review)
Result: Contract_v1_processed.docx (original with tracked changes from fallback applied)
```

### Requirements Mode (Existing)

**When to use:** You have a document with requirements, rules, or guidance text

**Process:**
1. Upload your main document
2. Upload a fallback document with requirements/guidance
3. System extracts requirements from the text
4. AI interprets requirements and generates appropriate edits
5. Edits are applied as tracked changes

## Features

### Tracked Change Detection

The system automatically detects:
- **Insertions**: Text that was added in the fallback document
- **Deletions**: Text that was removed in the fallback document
- **Substitutions**: Text that was replaced (delete + insert pair)

### Context Preservation

Each tracked change includes:
- The exact text that changed
- Surrounding context (50 characters before/after) for accurate matching
- Author attribution from the original change
- Date/time information
- Paragraph location

### Change Application

Tracked changes from the fallback document are applied to the main document with:
- New tracked changes showing the modifications
- Author attribution: Based on the fallback document author
- Change reason: "Based on tracked change by [Author] in fallback document"
- Context-aware matching to find the right location in the main document

## Using the Feature

### Via Streamlit UI

1. **Upload Main Document**
   - Click "1. Upload your main .docx file"
   - Select your document to be edited

2. **Enable Fallback Document**
   - Check "Use fallback document for guidance"
   - The fallback upload option will appear

3. **Upload Fallback Document**
   - Click "Upload fallback .docx file"
   - Select a document with tracked changes OR requirements text

4. **Process Document**
   - Add any additional user instructions (optional)
   - Click "✨ Process Document with New Changes"
   - The system will automatically detect if fallback has tracked changes

5. **Review Results**
   - Status message will indicate if tracked changes were used
   - Download the processed document with new tracked changes applied

### Via API

```python
import requests

# Prepare files
files = {
    'input_file': open('main_document.docx', 'rb'),
    'fallback_file': open('fallback_with_changes.docx', 'rb')
}

# Prepare form data
data = {
    'user_instructions': '',  # Optional additional instructions
    'author_name': 'AI Reviewer',
    'case_sensitive': True,
    'add_comments': True,
    'debug_mode': False,
    'merge_strategy': 'append'
}

# Call endpoint
response = requests.post(
    'http://localhost:8004/process-document-with-fallback/',
    files=files,
    data=data
)

# Check result
result = response.json()
print(f"Status: {result['status_message']}")
print(f"Edits applied: {result['edits_applied_count']}")
print(f"Method: {result.get('processing_method', 'Unknown')}")

# Download processed file
download_url = result['download_url']
```

## Technical Details

### Data Structures

**TrackedChange Dataclass:**
```python
@dataclass
class TrackedChange:
    change_type: str  # "insertion", "deletion", "substitution"
    old_text: str     # Text deleted (empty for insertion)
    new_text: str     # Text inserted (empty for deletion)
    author: str       # Author of the change
    date: str         # Date of the change
    paragraph_index: int
    context_before: str = ""  # Context for matching
    context_after: str = ""
```

### Processing Functions

1. **extract_tracked_changes_structured(docx_path)**: Extract tracked changes as TrackedChange objects
2. **convert_tracked_changes_to_edits(tracked_changes)**: Convert to edit dictionaries
3. **Backend endpoint**: Automatically detects and uses tracked changes if present

### Backend Workflow

```python
# 1. Check for tracked changes
tracked_changes = extract_tracked_changes_structured(fallback_path)

# 2. If found, use them directly
if tracked_changes:
    edits = convert_tracked_changes_to_edits(tracked_changes)
    # Skip LLM processing
else:
    # Fall back to requirements extraction and LLM processing
    fallback_instructions = generate_instructions_from_fallback(fallback_path)
    edits = get_llm_suggestions(doc_text, fallback_instructions)

# 3. Apply edits
process_document_with_edits(input_path, output_path, edits)
```

## Edge Cases and Handling

### No Tracked Changes in Fallback
- System automatically falls back to requirements extraction mode
- Status message: "...based on fallback document" (not "...from tracked changes")

### Mixed Content (Tracked Changes + Requirements Text)
- Tracked changes are prioritized and extracted first
- Requirements text mode is bypassed when tracked changes are found
- Future enhancement: Combine both modes

### Tracked Changes That Don't Match Main Document
- Text matching uses fuzzy matching with context
- Changes that can't be matched are logged
- Status message shows X out of Y changes applied
- Check processing log for details

### Pure Deletions vs. Substitutions
- Pure deletions (no new text) are included
- Substitutions (delete + insert) are detected and paired
- Context helps distinguish between adjacent changes

## Benefits

### Tracked Changes Mode
✅ **Faster**: No LLM processing needed
✅ **More Accurate**: Direct application of known changes
✅ **Preserves Intent**: Exact changes from the fallback document
✅ **Author Attribution**: Maintains original author information
✅ **No AI Costs**: Bypasses LLM when tracked changes are present

### Requirements Mode
✅ **Flexible**: Works with any guidance text
✅ **Interpretive**: AI understands complex requirements
✅ **Adaptive**: Generates appropriate changes for different contexts

## Debugging

### Enable Debug Mode

In the Streamlit UI:
- Set "Server Debugging Level" to "Standard Debugging" or "Extended Debugging"
- The debug panel will show:
  - Whether tracked changes were detected
  - Number of each type of change (insertions, deletions, substitutions)
  - Sample changes with old/new text
  - Processing method used

### Check Backend Logs

```bash
# In terminal where backend is running
docker-compose logs -f backend  # or
tail -f backend_logs.txt

# Look for messages like:
# [PID:xxx] Found 5 tracked changes in fallback document!
# [PID:xxx] Using tracked changes directly (bypassing LLM)
```

## Limitations

1. **Same Document Structure**: Works best when main and fallback documents have similar structure
2. **Text Matching**: Relies on text matching - significant document differences may cause issues
3. **Complex Changes**: Very complex multi-paragraph changes may need manual review
4. **Format Preservation**: Preserves content changes but may not preserve all formatting from fallback

## Future Enhancements

- [ ] Support for comment-based changes
- [ ] Hybrid mode: Combine tracked changes + requirements
- [ ] Change conflict detection
- [ ] Preview mode before applying changes
- [ ] Support for formatting changes (bold, italic, etc.)
- [ ] Multi-document fallback support

## FAQ

**Q: What if my fallback document has both tracked changes and requirements text?**
A: Currently, tracked changes take priority. Requirements text is ignored when tracked changes are present.

**Q: Can I use multiple fallback documents?**
A: Not yet. Currently only one fallback document is supported per processing request.

**Q: What Word formats are supported?**
A: .docx format only (Word 2007 and later)

**Q: Do I need to accept/reject tracked changes in the fallback document first?**
A: No - leave them as tracked changes. The system extracts unaccepted tracked changes.

**Q: Will this work with Google Docs?**
A: Export to .docx format first with tracked changes preserved.

## Examples

### Example 1: Legal Contract Review

```
Scenario: Apply legal team's changes to a contract

Main Document: Services_Agreement_v1.docx
Fallback Document: Services_Agreement_v1_legal_review.docx (with tracked changes)

Result: All legal changes applied as tracked changes in main document
```

### Example 2: Technical Documentation Update

```
Scenario: Apply technical reviewer's corrections

Main Document: API_Documentation.docx
Fallback Document: API_Documentation_reviewed.docx (with corrections as tracked changes)

Result: Technical corrections applied with reviewer attribution
```

### Example 3: Academic Paper Revision

```
Scenario: Apply co-author's suggestions

Main Document: Research_Paper_Draft1.docx
Fallback Document: Research_Paper_Draft1_coauthor_suggestions.docx (with tracked changes)

Result: Co-author suggestions applied as tracked changes for review
```

---

## See Also

- [NGINX_DEPLOYMENT_GUIDE.md](NGINX_DEPLOYMENT_GUIDE.md) - Deployment configuration
- [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) - Docker setup
- [CLAUDE.md](CLAUDE.md) - Project architecture overview
- [README.md](README.md) - General project information
