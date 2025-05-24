import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Optional

# Load environment variables from .env file (especially OPENAI_API_KEY)
# This is useful for local development. In production, prefer environment variables.
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY not found in environment variables or .env file.")
    # Potentially raise an error or handle this case as per your application's needs
    # For now, it will fail when trying to initialize OpenAI client without a key.

client = None
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)

def get_llm_suggestions(document_text: str, user_instructions: str, filename: str) -> Optional[List[Dict]]:
    """
    Sends the document text (or relevant parts) and user instructions to OpenAI
    to get suggestions for changes.

    Args:
        document_text (str): The text content of the Word document.
                             Consider sending only relevant paragraphs or a summary for large docs.
        user_instructions (str): The user's description of checks/changes.
        filename (str): Original filename, for context in logging or if needed by LLM.

    Returns:
        Optional[List[Dict]]: A list of dictionaries, where each dict represents an edit,
                              or None if an error occurs.
                              Expected format:
                              [
                                {
                                  "contextual_old_text": "The sentence containing the part to change.",
                                  "specific_old_text": "The exact text to find and delete.",
                                  "specific_new_text": "The text to insert.",
                                  "reason_for_change": "LLM's explanation for this change."
                                }
                              ]
    """
    if not client:
        print("OpenAI client not initialized. Please set OPENAI_API_KEY.")
        return None

    # Truncate document_text if it's too long to avoid excessive token usage/cost
    # Max tokens for gpt-3.5-turbo is around 4096 (prompt + completion)
    # This is a very rough truncation, consider more sophisticated methods.
    max_doc_text_length = 8000 # characters, roughly 2k tokens
    if len(document_text) > max_doc_text_length:
        document_text_snippet = document_text[:max_doc_text_length] + "\n... [document truncated] ..."
    else:
        document_text_snippet = document_text

    prompt = f"""
You are an expert editor tasked with revising a Word document based on user instructions.
The user has uploaded a document named '{filename}' and provided the following instructions:
"{user_instructions}"

Below is the text content extracted from the document (or a snippet if it's very long):
--- DOCUMENT TEXT ---
{document_text_snippet}
--- END DOCUMENT TEXT ---

Your task is to identify specific changes to be made to the document.
For each change, you MUST provide:
1.  `contextual_old_text`: A short piece of surrounding text from the original document that uniquely identifies the location of the change. This context should be distinctive enough for a program to find it. It should include the `specific_old_text`.
2.  `specific_old_text`: The exact text that needs to be replaced or deleted. This text MUST exist within the `contextual_old_text`.
3.  `specific_new_text`: The new text that should replace the `specific_old_text`. If the instruction is to delete text, provide an empty string "" for `specific_new_text`.
4.  `reason_for_change`: A brief explanation of why this change is being made, based on the user's instructions.

IMPORTANT:
- Ensure `specific_old_text` is an exact substring of `contextual_old_text`.
BBB- If no changes are needed based on the instructions, return an empty JSON list: [].
- If the instructions are unclear or cannot be mapped to specific text changes, return an empty JSON list.
- Pay close attention to preserving the original casing in `contextual_old_text` and `specific_old_text` as found in the document.
BBB- The `specific_new_text` should be what the user intends, including its casing.
BBB
Return your response as a JSON list of objects, where each object represents one change.
BBBBBBExample:
BBB[
BBB  {{
    "contextual_old_text": "The deadline for submission is May 1st, 2024, and all entries must comply.",
BBB    "specific_old_text": "May 1st, 2024",
    "specific_new_text": "June 5th, 2025",
    "reason_for_change": "Updated deadline as per user instruction to ensure deadlines are not before May 5th (example of a correction)."
  }},
  {{
    "contextual_old_text": "We need to complete the task very fast.",
    "specific_old_text": "very fast",
    "specific_new_text": "quickly",
    "reason_for_change": "Improved conciseness."
  }}
]

If user instructions are like "make sure deadlines are not before May 5th", and you find a date "April 10th", your `specific_old_text` would be "April 10th", `specific_new_text` would be the corrected date (e.g., "May 6th" or whatever is appropriate), and `contextual_old_text` would be the sentence containing "April 10th".

Provide only the JSON output. Do not include any other text or explanations outside the JSON structure.
"""

    try:
        print(f"Sending request to OpenAI. Instructions: {user_instructions[:100]}...")
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI assistant that helps identify text changes in a document based on user instructions and returns them in a specific JSON format."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-3.5-turbo-0125", # Or gpt-4 if preferred and available
            response_format={"type": "json_object"}, # For newer models that support JSON mode
            temperature=0.2, # Lower temperature for more deterministic output
        )
        
        response_content = chat_completion.choices[0].message.content
        print(f"LLM Raw Response: {response_content}")

        # The response_content should be a string containing JSON.
        # Sometimes the LLM might wrap the JSON in a key, e.g. {"edits": [...] }
        # Or it might just be the list [...]
        # We need to parse it carefully.
        try:
            # Attempt to parse the entire string as JSON
            parsed_json = json.loads(response_content)

            # Check if the parsed JSON is a list (as expected)
            if isinstance(parsed_json, list):
                # Validate structure of each item
                for item in parsed_json:
                    if not all(k in item for k in ["contextual_old_text", "specific_old_text", "specific_new_text", "reason_for_change"]):
                        print(f"LLM response item has missing keys: {item}")
                        # Handle malformed item, e.g., skip or return error
                        raise ValueError("LLM response item has missing keys.")
                return parsed_json
            # If the LLM wrapped the list in a dictionary (e.g., under a key like "edits" or "changes")
            elif isinstance(parsed_json, dict):
                # Try to find a list within the dictionary values
                for key, value in parsed_json.items():
                    if isinstance(value, list):
                        print(f"Found list of edits under key '{key}' in LLM response.")
                        # Validate structure of each item
                        for item in value:
                            if not all(k in item for k in ["contextual_old_text", "specific_old_text", "specific_new_text", "reason_for_change"]):
                                print(f"LLM response item (in dict) has missing keys: {item}")
                                raise ValueError("LLM response item (in dict) has missing keys.")
                        return value # Return the first list found
                print("LLM response was a JSON object but did not contain an identifiable list of edits.")
                return [] # Return empty list if no suitable list found
            else:
                print(f"LLM response was not a JSON list or a dict containing a list: {type(parsed_json)}")
                return []

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from LLM response: {e}")
            print(f"Problematic response content: {response_content}")
            # Attempt to extract JSON list if it's embedded in text
            match = re.search(r'\[\s*(\{.*?\}\s*(,\s*\{.*?\})*\s*)?\]', response_content, re.DOTALL)
            if match:
                json_like_part = match.group(0)
                try:
                    extracted_edits = json.loads(json_like_part)
                    print(f"Successfully extracted JSON list from problematic response: {extracted_edits}")
                    # Validate structure here too
                    for item in extracted_edits:
                        if not all(k in item for k in ["contextual_old_text", "specific_old_text", "specific_new_text", "reason_for_change"]):
                            raise ValueError("Extracted LLM response item has missing keys.")
                    return extracted_edits
                except json.JSONDecodeError:
                    print(f"Could not decode extracted JSON-like part: {json_like_part}")
                    return None # Or an empty list: []
            return None # Or an empty list: []
        except ValueError as e: # For custom validation errors
            print(f"LLM response validation error: {e}")
            return None

    except Exception as e:
        print(f"An error occurred while calling OpenAI API: {e}")
        return None

if __name__ == '__main__':
    # Example usage (for testing this module directly)
    if not OPENAI_API_KEY:
        print("Cannot run test: OPENAI_API_KEY is not set.")
    else:
        sample_doc_text = """
        This is the first paragraph. The event is scheduled for April 10th, 2023. We must ensure quality.
        The second paragraph discusses old_project_name which needs an update.
        Another important date is March 15, 2023.
        Final review meetings are on April 20th, 2023.
        """
        sample_instructions = "Please change all dates before May 1st, 2023 to June 1st, 2024. Also, rename 'old_project_name' to 'new_project_alpha'."
        
        print(f"\n--- Testing LLM Handler with sample data ---")
        print(f"Document Text Snippet:\n{sample_doc_text[:200]}...")
        print(f"User Instructions: {sample_instructions}")

        suggestions = get_llm_suggestions(sample_doc_text, sample_instructions, "sample_document.docx")

        if suggestions is not None:
            print("\n--- LLM Suggestions Received ---")
            if suggestions:
                for i, suggestion in enumerate(suggestions):
                    print(f"\nSuggestion {i+1}:")
                    print(f"  Context: '{suggestion.get('contextual_old_text')}'")
                    print(f"  Old Text: '{suggestion.get('specific_old_text')}'")
                    print(f"  New Text: '{suggestion.get('specific_new_text')}'")
                    print(f"  Reason: '{suggestion.get('reason_for_change')}'")
            else:
                print("No suggestions were generated by the LLM (empty list returned).")
        else:
            print("\n--- Failed to get suggestions from LLM ---")
