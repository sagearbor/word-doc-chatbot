import json
import re
from typing import List, Dict, Optional, Any

from .ai_client import get_chat_response # Assuming .ai_client is in the same directory or correctly pathed

# --- Function for Approach 1: Summarizing a pre-parsed list of changes ---
def get_llm_analysis_from_summary(changes_summary_text: str, filename: str) -> Optional[str]:
    """
    Sends a pre-parsed summary of tracked changes to the LLM for a high-level analysis.
    """
    # Handle cases where extraction found no changes or had an error
    if changes_summary_text.startswith("No tracked insertions or deletions"):
        return "The document analysis indicates that no tracked changes (insertions or deletions) were found to summarize."
    if changes_summary_text.startswith("Error_Internal:"): # Pass through internal errors from word_processor
        return changes_summary_text # e.g., "Error_Internal: Could not open document..."

    prompt = (
        f"You are an expert editor. Below is a summary of tracked changes (insertions and deletions) "
        f"extracted from the Word document named '{filename}'.\n\n"
        "Your task is to provide a concise, high-level textual summary of what these changes "
        "collectively suggest or aim to achieve. For example, are the changes mostly stylistic, "
        "correcting typos, updating specific information (like names, dates, or figures), "
        "rephrasing for clarity, adding new sections, or deleting obsolete content?\n\n"
        "Focus on the overall themes, patterns, or main purposes of the edits as indicated by the provided summary of changes.\n\n"
        "Summary of Tracked Changes:\n"
        "---------------------------\n"
        f"{changes_summary_text}\n"
        "---------------------------\n\n"
        "Please return only your high-level summary of these changes in plain text."
    )
    system_prompt = "You are an AI assistant specialized in summarizing the purpose and themes of tracked changes in a document, based on an input list of those changes."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    try:
        response = get_chat_response(messages, temperature=0.2, max_tokens=800) # Max output tokens
        return response
    except Exception as e:
        print(f"An error occurred while calling AI provider for analysis of changes summary: {e}")
        return "Error_AI: The AI service could not provide an analysis for the tracked changes summary at this time."

# --- Function for Approach 2: Analyzing raw document.xml content ---
def get_llm_analysis_from_raw_xml(document_xml_content: str, filename: str) -> Optional[str]:
    """
    Sends the raw word/document.xml content to the LLM for it to find and summarize changes.
    """
    if document_xml_content.startswith("Error_Internal:"): # Pass through internal errors from word_processor
        return document_xml_content

    # Heuristic: if the content is extremely short, it's likely not valid XML or an error occurred
    if len(document_xml_content) < 200: # Arbitrary short length, <w:document> itself is ~100
         print(f"[LLM_HANDLER_DEBUG] Raw XML content for '{filename}' seems too short ({len(document_xml_content)} chars). Passing to LLM but might indicate issue.")
         # Could return "Error_Input: The provided XML content from the document seems too short or invalid to process."

    # Truncate very long XML for the prompt to avoid excessive token usage *in the prompt itself*.
    # The LLM's ability to process very long *inputs* (even if truncated in prompt) depends on its context window.
    MAX_XML_CHARS_IN_PROMPT = 30000  # Approx 7.5k tokens, adjust based on your LLM's limits for the prompt
    xml_for_prompt_display = document_xml_content
    if len(document_xml_content) > MAX_XML_CHARS_IN_PROMPT:
        xml_for_prompt_display = document_xml_content[:MAX_XML_CHARS_IN_PROMPT] + \
                                 f"\n... [XML CONTENT TRUNCATED IN PROMPT - Original length: {len(document_xml_content)} characters] ..."
        print(f"[LLM_HANDLER_DEBUG] Raw XML content for '{filename}' was truncated in the prompt display.")

    prompt = (
        f"You are an AI assistant highly skilled in parsing WordProcessingML XML from Microsoft Word documents.\n"
        f"The following is the content of the 'word/document.xml' file from a .docx document named '{filename}'. "
        f"This XML may be very long and complex.\n\n"
        "--- XML CONTENT START ---\n"
        f"{xml_for_prompt_display}\n" # Use the potentially truncated version for display in prompt
        "--- XML CONTENT END ---\n\n"
        "Please carefully analyze this XML content. Your primary goal is to identify all tracked changes. "
        "Look for <w:ins> (insertion) elements and <w:del> (deletion) elements. For each, try to determine "
        "the inserted text (from <w:t> within <w:ins>) or deleted text (from <w:delText> within <w:del>). "
        "Also, note the 'w:author' and 'w:date' attributes if available for these changes.\n"
        "Based on all the insertions and deletions you can identify from this raw XML, provide a concise, "
        "high-level textual summary of what these changes collectively achieve or suggest. "
        "For example, are they stylistic, correcting typos, updating specific information, etc.?\n\n"
        "If the XML is too complex or seems truncated, and you cannot reliably identify changes, please state that clearly.\n"
        "Return only your high-level summary of these identified changes in plain text."
    )
    system_prompt = "You are an AI assistant that parses raw WordProcessingML XML to find and summarize tracked changes."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    try:
        # For raw XML, the LLM might need a larger context window and more output tokens if it tries to quote things.
        response = get_chat_response(messages, temperature=0.2, max_tokens=1000) # Max output tokens
        return response
    except Exception as e:
        print(f"An error occurred while calling AI provider for raw XML analysis: {e}")
        return "Error_AI: The AI service could not provide an analysis from the raw XML at this time."


def get_llm_suggestions(document_text: str, user_instructions: str, filename: str) -> List[Dict]:
    # ... (keep existing get_llm_suggestions as it's for a different functionality) ...
    max_doc_snippet_len = 7500 
    doc_snippet = document_text
    if len(document_text) > max_doc_snippet_len:
        doc_snippet = document_text[:max_doc_snippet_len] + "\n... [DOCUMENT TRUNCATED] ..."
    print("\n[LLM_HANDLER_DEBUG] Document snippet being sent to LLM for suggestions:")
    print(doc_snippet[:1000] + "..." if len(doc_snippet) > 1000 else doc_snippet)
    print(f"(Total snippet length: {len(doc_snippet)})")
    print("[LLM_HANDLER_DEBUG] End of document snippet for suggestions.\n")
    prompt = f"""You are an AI assistant that suggests specific textual changes for a Word document based on user instructions.
Your goal is to identify the exact text to be replaced (`specific_old_text`), provide enough surrounding text for unique identification in the document (`contextual_old_text`), the new text (`specific_new_text`), and a reason for the change.
**IMPORTANT: The user's instructions may request multiple, independent changes. You MUST identify and list ALL such changes. Process the ENTIRE set of user instructions and generate a separate JSON object for EACH distinct edit identified.**
User instructions for changes: {user_instructions}
**Critical Instructions for Defining `specific_old_text`:**
1.  **Target Complete Semantic Units:**
    * You *must* ensure `specific_old_text` represents the entire, complete semantic unit in the document that needs changing.
    * **Numbers and Currency:** If a numerical value like "USD150.25" or "75%" needs modification, `specific_old_text` must be the *entire value* (e.g., "USD150.25", not just "150"; "75%", not just "75"). If the document says "cost is $101" and the intent is to change this amount, `specific_old_text` must be "$101". Do *not* suggest changing only a part like "$10" if it's found within a larger number like "$101".
    * **Words and Proper Nouns:** `specific_old_text` must capture the whole word or relevant multi-word proper noun/phrase. For example, if changing "inter-disciplinary approach", `specific_old_text` should be "inter-disciplinary approach". Avoid partial word selections like "disciplinary" from "inter-disciplinary".
2.  **Boundary Adherence for `specific_old_text`:**
    * The processing script will verify that your chosen `specific_old_text`, when found in the document, is appropriately bounded. This means:
        * The character immediately *before* your `specific_old_text` in the document should be whitespace (space, tab, etc.) or it should be the beginning of a paragraph.
        * The character immediately *after* your `specific_old_text` in the document should be whitespace, or one of the following punctuation marks: comma (,), period (.), semicolon (;), or it should be the end of a paragraph.
    * **Your primary task is to select the correct full token that also meets these boundary conditions in the original text.** For instance, if `specific_old_text` is "item" and the document text is "item.", this selection is valid. If `specific_old_text` is "item" and the document text is "items", this selection is invalid because "s" is not an allowed boundary character.
3.  **Examples of Correct `specific_old_text` Identification:**
    * Document Text: "...the initial fee was EUR75.50 and..."
        LLM Goal: Change the fee to EUR90.
        Correct `specific_old_text`: "EUR75.50"
    * Document Text: "...for all client-focused initiatives..."
        LLM Goal: Change "client-focused" to "customer-centric".
        Correct `specific_old_text`: "client-focused"
    * Document Text: "The item, a widget, was blue."
        LLM Goal: Change "widget" to "gadget".
        Correct `specific_old_text`: "widget"
**Output Format Instructions:**
Return your suggestions *only* as a valid JSON structure. This structure **MUST be a flat JSON array of objects**, where each object has the keys: "contextual_old_text", "specific_old_text", "specific_new_text", "reason_for_change".
Example of correct flat array: `[ {{"contextual_old_text": "...", "specific_old_text": "...", "specific_new_text": "...", "reason_for_change": "..."}}, {{"contextual_old_text": "...", "specific_old_text": "...", "specific_new_text": "...", "reason_for_change": "..."}} ]`
If only one change is suggested, you **MUST still return it as an array with one object**: `[ {{"contextual_old_text": "...", "specific_old_text": "...", "specific_new_text": "...", "reason_for_change": "..."}} ]`
If no changes are needed based on the user instructions and the document, or if no changes can be identified that meet all the above criteria, return an empty JSON list: `[]`.
**DO NOT return a list containing another list, a single JSON object that is not an array, or a list containing null values. The top-level response MUST be a JSON array `[...]`.**
Document (`{filename}`), snippet if long:
{doc_snippet}
"""
    messages = [{"role": "user", "content": prompt}]
    content: Optional[str] = None
    try:
        content = get_chat_response(messages, temperature=0.1, response_format={"type": "json_object"})
        if not content:
            print("LLM returned empty content for suggestions.")
            return [] 
    except Exception as e:
        print(f"LLM call for suggestions failed: {e}")
        return [] 
    edits: List[Dict] = []
    try:
        edits = _parse_llm_response(content) 
    except Exception as e_parse:
        print(f"Critical error during _parse_llm_response after LLM call: {e_parse}")
        print(f"Content given to _parse_llm_response (snippet): {content[:500] if content else 'None'}")
        return []
    valid_edits: List[Dict] = []
    required_keys = {"contextual_old_text", "specific_old_text", "reason_for_change"}
    for i, edit_item in enumerate(edits): 
        if isinstance(edit_item, dict) and required_keys.issubset(edit_item.keys()):
            if all(isinstance(edit_item.get(key), str) for key in ["contextual_old_text", "specific_old_text", "reason_for_change"]) and \
               (edit_item.get("specific_new_text") is None or isinstance(edit_item.get("specific_new_text"), str)):
                valid_edits.append(edit_item)
            else:
                print(f"Skipping edit item {i+1} due to incorrect data types for required keys: {edit_item}.")
        else:
            print(f"Skipping edit item {i+1} due to missing keys or not being a dictionary: {edit_item}. Required: {required_keys}")
    return valid_edits

def _parse_llm_response(content: str) -> List[Dict]:
    # ... (keep existing _parse_llm_response) ...
    if not content or not content.strip():
        print("LLM response content is empty.")
        return []
    json_str_to_parse: Optional[str] = None
    try:
        json_array_match = re.search(r'\[.*\]', content, re.DOTALL | re.MULTILINE)
        json_object_match = re.search(r'\{.*\}', content, re.DOTALL | re.MULTILINE)
        if json_array_match: json_str_to_parse = json_array_match.group(0)
        elif json_object_match: json_str_to_parse = json_object_match.group(0)
        if not json_str_to_parse:
            if content.strip().startswith(('[', '{')) and content.strip().endswith((']', '}')):
                json_str_to_parse = content.strip()
            else:
                print(f"Could not find a clear JSON array or object structure in LLM response. Content: {content[:500]}")
                return []
        data: Any = json.loads(json_str_to_parse)
        if isinstance(data, list):
            if data and isinstance(data[0], list):
                potential_edits = [item for item in data[0] if isinstance(item, dict)]
                if potential_edits:
                    print(f"LLM returned a nested list; extracted {len(potential_edits)} edits from the inner list.")
                    return potential_edits
                else:
                    print("LLM returned a nested list, but the inner list was empty or had no dictionaries.")
                    return []
            elif all(isinstance(item, dict) for item in data): return data
            else:
                print(f"LLM returned a list, but not all items are dictionaries, nor is it a list of a list of dictionaries: {str(data)[:300]}")
                return []
        elif isinstance(data, dict):
            required_keys = {"contextual_old_text", "specific_old_text", "reason_for_change"}
            if required_keys.issubset(data.keys()): return [data] 
            for key in data:
                if isinstance(data[key], list):
                    if all(isinstance(item, dict) for item in data[key]): return data[key]
            print(f"LLM response was a dict, but not a single edit and no list of edits found within it: {str(data)[:300]}")
            return []
        else:
            print(f"LLM response could not be parsed into a list or dictionary of edits. Parsed data type: {type(data)}")
            return []
    except json.JSONDecodeError as exc:
        parsed_str_snippet = json_str_to_parse[:500] if json_str_to_parse else "N/A (json_str_to_parse was None)"
        print(f"Could not decode JSON from LLM response. Error: {exc}\nString attempted to parse: '{parsed_str_snippet}...' \nOriginal content snippet: '{content[:500]}...'")
    except Exception as e:
        print(f"An unexpected error occurred during LLM response parsing: {type(e).__name__}: {e}\nContent snippet: {content[:500]}")
    return []


if __name__ == "__main__":
    # ... (keep existing __main__ block for testing if desired) ...
    sample_doc_text = (
        "This document outlines the project plan. The deadline for Phase 1 is 2024-07-15. "
        "The primary contact is Mr. Smitherson. Budget allocation is $10100. " 
        "We need to ensure quality control throughout the process. The final report is due on 2024-09-30."
        "Also, the old policy reference X123 needs updating."
        "The cost would be $101 , to a new number."
        "MrArbor is the author. Bob and another Bob are here."
    )
    user_instructions_test = (
        "Change Mr. Smitherson to Ms. Jones. Update the budget from $10100 to $12000. "
        "The deadline for Phase 1 should be 2024-08-01. Ensure 'quality control' is changed to 'quality assurance'. "
        "Replace policy X123 with Y456."
        "Change $101 to $208. Change MrArbor to MrSage. Change all Bob to Robert."
    )
    print("Requesting LLM suggestions (simulated - actual call commented out for safety)...")
    print("\n--- Testing _parse_llm_response with problematic input ---")
    problematic_llm_content = """
    ```json
    [
      [
        {
          "contextual_old_text": "the cost would be $101",
          "specific_old_text": "$101",
          "specific_new_text": "$208",
          "reason_for_change": "The cost should be at least $208."
        },
        {
          "contextual_old_text": "last edited by MrArbor",
          "specific_old_text": "MrArbor",
          "specific_new_text": "MrSage",
          "reason_for_change": "Change MrArbor to MrSage."
        }
      ], null, [ {"contextual_old_text": "another item", "specific_old_text": "item", "specific_new_text": "thing", "reason_for_change": "just because"} ]
    ]
    ```
    """
    parsed_problematic = _parse_llm_response(problematic_llm_content)
    print("Parsed problematic content:")
    print(json.dumps(parsed_problematic, indent=2) if parsed_problematic else "Failed to parse problematic content or got empty list.")
    print("\n--- Testing _parse_llm_response with a good flat list ---")
    good_llm_content = """
    ```json
    [ {"contextual_old_text": "the cost would be $101", "specific_old_text": "$101", "specific_new_text": "$208", "reason_for_change": "The cost should be at least $208."} ]
    ```
    """
    parsed_good = _parse_llm_response(good_llm_content)
    print("Parsed good content:")
    print(json.dumps(parsed_good, indent=2) if parsed_good else "Failed to parse good content.")
    print("\nNote: Actual LLM call is commented out in __main__ to prevent unintended API calls during simple script run.")