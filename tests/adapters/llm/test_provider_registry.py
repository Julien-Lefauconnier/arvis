# tests/adapters/llm/test_provider_registry.py

import pytest

from arvis.adapters.llm.providers.registry import build_provider


def test_build_mock_provider() -> None:
    provider = build_provider("mock")
    assert provider is not None


def test_build_provider_is_case_insensitive() -> None:
    provider = build_provider("MOCK")
    assert provider is not None


def test_unknown_provider_raises() -> None:
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        build_provider("unknown")
