import os
import sys
import types
import pytest

if 'dotenv' not in sys.modules:
    sys.modules['dotenv'] = types.SimpleNamespace(load_dotenv=lambda *a, **k: None)

from backend.config import AIConfig


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError):
        AIConfig.get_api_key("openai")


def test_get_current_provider_default(monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    assert AIConfig.get_current_provider() == "openai"
