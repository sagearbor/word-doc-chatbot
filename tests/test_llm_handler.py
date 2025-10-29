from backend.llm_handler import _parse_llm_response


def test_parse_llm_response_list():
    content = '[{"contextual_old_text": "old", "specific_old_text": "old", "specific_new_text": "new", "reason_for_change": "test"}]'
    result = _parse_llm_response(content)
    assert isinstance(result, list)
    assert result[0]["specific_new_text"] == "new"


def test_parse_llm_response_invalid_json():
    assert _parse_llm_response("not json") is None
