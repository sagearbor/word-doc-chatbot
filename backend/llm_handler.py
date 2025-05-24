import os
import json
from typing import List, Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI

# Load .env if present so developers can store OPENAI_API_KEY locally
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client: Optional[OpenAI] = None
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)


def _parse_llm_response(content: str) -> Optional[List[Dict]]:
    """Parse the JSON list returned by the LLM."""
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


if __name__ == "__main__":
    sample_doc = "The deliverable is due in three months."
    sample_inst = "Ensure deliverables are not due in less than six months."
    suggestions = get_llm_suggestions(sample_doc, sample_inst, "sample.docx")
    print(json.dumps(suggestions, indent=2))
