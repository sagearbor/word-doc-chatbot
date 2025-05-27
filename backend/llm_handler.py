import json
import re
from typing import List, Dict, Optional, Any # Added Any

# Assuming .ai_client is in the same directory or correctly pathed
from .ai_client import get_ai_response, get_chat_response 


def get_llm_analysis(document_text: str, filename: str) -> Optional[str]:
    # ... (this function seems okay for now)
    snippet = document_text[:8000] 
    if len(document_text) > 8000:
        snippet += "\n... [document truncated for brevity] ..."

    prompt = (
        f"You are an expert editor reviewing the Word document '{filename}'.\n"
        "Provide a concise numbered list summarizing potential improvements.\n"
        "Focus on win-win modifications that would improve the document for all parties.\n"
        "Suggest how the user might instruct an AI to implement these changes,\n"
        "such as offering higher quality wording in exchange for additional budget.\n\n"
        "Document text (or snippet thereof):\n"
        "---\n"
        f"{snippet}\n"
        "---\n"
        "Please return only the numbered list of recommendations in plain text format."
    )

    system_prompt = "You are an AI assistant that analyzes documents and proposes improvements as a concise, numbered list."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    try:
        response = get_chat_response(messages, temperature=0.3, max_tokens=1000)
        return response
    except Exception as e:
        print(f"An error occurred while calling AI provider for analysis: {e}")
        return None


def _parse_llm_response(content: str) -> List[Dict]: # Ensure return is always List[Dict]
    if not content or not content.strip():
        print("LLM response content is empty.")
        return []

    json_str_to_parse: Optional[str] = None
    try:
        # Try to find a JSON array '[...]' or object '{...}' within the content.
        json_array_match = re.search(r'\[.*\]', content, re.DOTALL | re.MULTILINE)
        json_object_match = re.search(r'\{.*\}', content, re.DOTALL | re.MULTILINE)

        if json_array_match:
            json_str_to_parse = json_array_match.group(0)
        elif json_object_match:
            json_str_to_parse = json_object_match.group(0)
        
        if not json_str_to_parse:
            if content.strip().startswith(('[', '{')) and content.strip().endswith((']', '}')):
                json_str_to_parse = content.strip()
            else:
                print(f"Could not find a clear JSON array or object structure in LLM response. Content: {content[:500]}")
                return []

        data: Any = json.loads(json_str_to_parse)
        
        # --- NEW LOGIC TO HANDLE NESTED LIST ---
        if isinstance(data, list):
            # Check if the first element is itself a list (potential actual list of edits)
            # And also ensure it's not an empty list before trying to access data[0]
            if data and isinstance(data[0], list):
                # The actual edits are in the first element (the inner list)
                # Filter this inner list to ensure all its items are dictionaries
                potential_edits = [item for item in data[0] if isinstance(item, dict)]
                if potential_edits: # If we found some dicts in the inner list
                     # Further validation can be done here if needed (e.g. check for required keys)
                    print(f"LLM returned a nested list; extracted {len(potential_edits)} edits from the inner list.")
                    return potential_edits
                else: # Inner list was empty or contained no dicts
                    print("LLM returned a nested list, but the inner list was empty or had no dictionaries.")
                    return []
            # Original case: data is already a flat list of edits
            elif all(isinstance(item, dict) for item in data):
                return data
            else: # data is a list, but not of dicts, and not a list containing a list of dicts
                print(f"LLM returned a list, but not all items are dictionaries, nor is it a list of a list of dictionaries: {str(data)[:300]}")
                return []
        # --- END OF NEW LOGIC ---
        
        elif isinstance(data, dict):
            required_keys = {"contextual_old_text", "specific_old_text", "reason_for_change"} # specific_new_text is optional
            if required_keys.issubset(data.keys()): # Check if dict itself could be an edit
                return [data] 
            for key in data: # Check if any key in the dict contains a list of edits
                if isinstance(data[key], list):
                    if all(isinstance(item, dict) for item in data[key]):
                        return data[key]
            print(f"LLM response was a dict, but not a single edit and no list of edits found within it: {str(data)[:300]}")
            return []
        else: # data is not a list or a dict
            print(f"LLM response could not be parsed into a list or dictionary of edits. Parsed data type: {type(data)}")
            return []

    except json.JSONDecodeError as exc:
        parsed_str_snippet = json_str_to_parse[:500] if json_str_to_parse else "N/A (json_str_to_parse was None)"
        print(f"Could not decode JSON from LLM response. Error: {exc}\nString attempted to parse: '{parsed_str_snippet}...' \nOriginal content snippet: '{content[:500]}...'")
    except Exception as e:
        print(f"An unexpected error occurred during LLM response parsing: {type(e).__name__}: {e}\nContent snippet: {content[:500]}")
    
    return []


def get_llm_suggestions(document_text: str, user_instructions: str, filename: str) -> List[Dict]:
    max_doc_snippet_len = 7500 
    doc_snippet = document_text
    if len(document_text) > max_doc_snippet_len:
        doc_snippet = document_text[:max_doc_snippet_len] + "\n... [DOCUMENT TRUNCATED] ..."
    
    # ---- ADDING DEBUG PRINT FOR SNIPPET SENT TO LLM ----
    print("\n[LLM_HANDLER_DEBUG] Document snippet being sent to LLM for suggestions:")
    print(doc_snippet[:1000] + "..." if len(doc_snippet) > 1000 else doc_snippet)
    print(f"(Total snippet length: {len(doc_snippet)})")
    print("[LLM_HANDLER_DEBUG] End of document snippet for suggestions.\n")
    # ---- END OF DEBUG PRINT ----

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
    messages = [{"role": "user", "content": prompt}] # System prompt could also be used here
    content: Optional[str] = None
    try:
        # Ensure your AI client is configured to expect JSON and ideally enforce it.
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
    required_keys = {"contextual_old_text", "specific_old_text", "reason_for_change"} # specific_new_text is optional
    for i, edit_item in enumerate(edits): 
        if isinstance(edit_item, dict) and required_keys.issubset(edit_item.keys()):
            # Basic type validation for critical fields
            if all(isinstance(edit_item.get(key), str) for key in ["contextual_old_text", "specific_old_text", "reason_for_change"]) and \
               (edit_item.get("specific_new_text") is None or isinstance(edit_item.get("specific_new_text"), str)): # new_text can be empty string or None
                valid_edits.append(edit_item)
            else:
                print(f"Skipping edit item {i+1} due to incorrect data types for required keys: {edit_item}.")
        else:
            print(f"Skipping edit item {i+1} due to missing keys or not being a dictionary: {edit_item}. Required: {required_keys}")
            
    return valid_edits

# ... (rest of llm_handler.py, including __main__, is assumed unchanged) ...
if __name__ == "__main__":
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
    
    # To test get_llm_suggestions properly, uncomment and ensure your .ai_client is configured.
    # suggestions = get_llm_suggestions(sample_doc_text, user_instructions_test, "test_document.docx")
    # print("\nLLM Suggestions Parsed:")
    # if suggestions:
    #     print(json.dumps(suggestions, indent=2))
    # else:
    #     print("No valid suggestions parsed or LLM returned empty.")

    # For now, let's demonstrate the _parse_llm_response with the problematic structure
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
      ],
      null,
      [ 
        {
            "contextual_old_text": "another item",
            "specific_old_text": "item",
            "specific_new_text": "thing",
            "reason_for_change": "just because"
        }
      ]
    ]
    ```
    """
    parsed_problematic = _parse_llm_response(problematic_llm_content)
    print("Parsed problematic content:")
    print(json.dumps(parsed_problematic, indent=2) if parsed_problematic else "Failed to parse problematic content or got empty list.")
    # Expected: should extract the first inner list, and ignore the null and the second inner list based on current logic
    # Or, if we want to merge all inner lists that are lists of dicts:
    
    print("\n--- Testing _parse_llm_response with a good flat list ---")
    good_llm_content = """
    ```json
    [
        {
          "contextual_old_text": "the cost would be $101",
          "specific_old_text": "$101",
          "specific_new_text": "$208",
          "reason_for_change": "The cost should be at least $208."
        }
    ]
    ```
    """
    parsed_good = _parse_llm_response(good_llm_content)
    print("Parsed good content:")
    print(json.dumps(parsed_good, indent=2) if parsed_good else "Failed to parse good content.")


    print("\n--- Full Prompt for LLM (for display/manual testing) ---")
    # (Construct and print the full prompt as in your llm_handler.py __main__ if needed for manual testing with an LLM)
    # ...
    print("\nNote: Actual LLM call is commented out in __main__ to prevent unintended API calls during simple script run.")
    print("To test live, uncomment the call to get_llm_suggestions and ensure your .ai_client is configured.")