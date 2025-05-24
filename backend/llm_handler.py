import os
import json
from typing import List, Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env if present
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY not found in environment variables or .env file.")

client: Optional[OpenAI] = None
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)


def get_llm_analysis(document_text: str, filename: str) -> Optional[str]:
    """Ask the LLM to analyze the document and suggest improvements."""
    if not client:
        print("OpenAI client not initialized. Please set OPENAI_API_KEY.")
        return None

    snippet = document_text[:8000]
    if len(document_text) > 8000:
        snippet += "\n... [document truncated] ..."

    prompt = f"""
      You are an expert editor reviewing the Word document '{filename}'.
      Provide a concise numbered list summarizing potential improvements.
      Focus on win-win modifications that would improve the document for all parties.
      Suggest how the user might instruct an AI to implement these changes,
      such as offering higher quality wording in exchange for additional budget.

      Document text (snippet if long):
      ---
      {snippet}
      ---
      Return only the numbered list of recommendations in plain text.
      """
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You analyze documents and propose improvements in a concise numbered list."},
                {"role": "user", "content": prompt},
            ],
            model="gpt-3.5-turbo-0125",
            temperature=0.3,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"An error occurred while calling OpenAI for analysis: {e}")
        return None


def _parse_llm_response(content: str) -> Optional[List[Dict]]:
    """Parse the JSON list returned by the LLM."""
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for val in data.values():
                if isinstance(val, list):
                    return val
    except json.JSONDecodeError as exc:
        print(f"Could not decode JSON from LLM response: {exc}\nContent: {content}")
    return None


def get_llm_suggestions(document_text: str, user_instructions: str, filename: str) -> Optional[List[Dict]]:
    """Return a list of edit instructions for word_processor."""
    if not client:
        # Allow local testing without an API key
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


if __name__ == "__main__":
    sample_doc = "The deliverable is due in three months."
    sample_inst = "Ensure deliverables are not due in less than six months."
    suggestions = get_llm_suggestions(sample_doc, sample_inst, "sample.docx")
    print(json.dumps(suggestions, indent=2))
