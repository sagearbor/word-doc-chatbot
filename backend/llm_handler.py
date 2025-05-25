import json
from typing import List, Dict, Optional

from .ai_client import get_ai_response, get_chat_response


def get_llm_analysis(document_text: str, filename: str) -> Optional[str]:
    """Ask the LLM to analyze the document and suggest improvements using the current AI provider."""
    snippet = document_text[:8000]
    if len(document_text) > 8000:
        snippet += "\n... [document truncated] ..."

    prompt = (
        f"You are an expert editor reviewing the Word document '{filename}'.\n"
        "Provide a concise numbered list summarizing potential improvements.\n"
        "Focus on win-win modifications that would improve the document for all parties.\n"
        "Suggest how the user might instruct an AI to implement these changes,\n"
        "such as offering higher quality wording in exchange for additional budget.\n\n"
        "Document text (snippet if long):\n"
        "---\n"
        f"{snippet}\n"
        "---\n"
        "Return only the numbered list of recommendations in plain text."
    )

    system_prompt = "You analyze documents and propose improvements in a concise numbered list."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    try:
        response = get_chat_response(messages, temperature=0.3)
        return response
    except Exception as e:
        print(f"An error occurred while calling AI provider for analysis: {e}")
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
    """Return a list of edit instructions for word_processor using the current AI provider."""
    prompt = (
        "You are an assistant that suggests edits to a Word document. "
        "Return only a JSON array of objects with the keys: contextual_old_text, "
        "specific_old_text, specific_new_text, reason_for_change. "
        "If no changes are needed return an empty JSON list.\n\n"
        f"User instructions: {user_instructions}\n\nDocument snippet:\n{document_text[:8000]}"
    )
    messages = [{"role": "user", "content": prompt}]
    try:
        content = get_chat_response(messages, temperature=0.2, response_format={"type": "json_object"})
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
