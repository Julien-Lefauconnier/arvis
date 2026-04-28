# tests/adapters/llm/test_llm_provider_imports.py

import pytest


def test_anthropic_provider_import_guard() -> None:
    from arvis.adapters.llm.providers import AnthropicProvider

    with pytest.raises(ImportError):
        AnthropicProvider()


def test_ollama_provider_import_guard() -> None:
    from arvis.adapters.llm.providers import OllamaProvider

    with pytest.raises(ImportError):
        OllamaProvider()
