import os
import json
from typing import List, Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI
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
   
def _parse_llm_response(content: str) -> Optional[List[Dict]]:
    """Parse the JSON list returned by the LLM."""    
    """
    <<<<<<< codex/review-and-improve-environment-based-url-handling
    Your task is to identify specific changes to be made to the document.
    For each change, you MUST provide:
    1.  `contextual_old_text`: A short piece of surrounding text from the original document that uniquely identifies the location of the change. This context should be distinctive enough for a program to find it. It should include the `specific_old_text`.
    2.  `specific_old_text`: The exact text that needs to be replaced or deleted. This text MUST exist within the `contextual_old_text`.
    3.  `specific_new_text`: The new text that should replace the `specific_old_text`. If the instruction is to delete text, provide an empty string "" for `specific_new_text`.
    4.  `reason_for_change`: A brief explanation of why this change is being made, based on the user's instructions.

    IMPORTANT:
    - Ensure `specific_old_text` is an exact substring of `contextual_old_text`.
      - If no changes are needed based on the instructions, return an empty JSON list: [].
    - If the instructions are unclear or cannot be mapped to specific text changes, return an empty JSON list.
    - Pay close attention to preserving the original casing in `contextual_old_text` and `specific_old_text` as found in the document.
      - The `specific_new_text` should be what the user intends, including its casing.

    Return your response as a JSON list of objects, where each object represents one change.
      Example:
      [
        {{
          "contextual_old_text": "The deadline for submission is May 1st, 2024, and all entries must comply.",
          "specific_old_text": "May 1st, 2024",
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
    """ 
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            # Some models may wrap the list under a key like "edits"
            for val in data.values():
                if isinstance(val, list):
                    return val
    except json.JSONDecodeError as exc:
        print(f"Could not decode JSON from LLM response: {exc}\nContent: {content}")
    return None

def get_llm_suggestions(document_text: str, user_instructions: str, filename: str) -> Optional[List[Dict]]:
    """Return a list of edit instructions for word_processor."""
    if not client:
        # When no API key is configured we simply return an empty list so the
        # rest of the pipeline can still run during local testing.
        print("OpenAI API key not configured - returning no suggestions.")
        return []

    prompt = (
        "You are an assistant that suggests edits to a Word document. "
        "Return only a JSON array of objects with the keys: contextual_old_text, "
        "specific_old_text, specific_new_text, reason_for_change. "
        "If no changes are needed return an empty JSON list.\n\n"
        f"User instructions: {user_instructions}\n\nDocument snippet:\n{document_text[:8000]}"
    )

    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        content = resp.choices[0].message.content
    except Exception as e:  # pragma: no cover - network
        print(f"LLM call failed: {e}")
        return None

    edits = _parse_llm_response(content)
    if edits is None:
        print("LLM response could not be parsed")
        return None
    return edits

# Keep the detailed logging from your branch (it's useful for debugging)
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

# And add the test code from main (but fix the syntax error)
if __name__ == "__main__":
    sample_doc = "The deliverable is due in three months."
    sample_inst = "Ensure deliverables are not due in less than six months."
    suggestions = get_llm_suggestions(sample_doc, sample_inst, "sample.docx")
    print(json.dumps(suggestions, indent=2))
    