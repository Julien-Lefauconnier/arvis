# tests/adapters/llm/test_provider_resolver.py

from arvis.adapters.llm.providers import LLMProviderSettings, MockLLMProvider
from arvis.adapters.llm.providers.resolver import resolve_provider


def test_resolve_provider_defaults_to_mock() -> None:
    provider = resolve_provider(LLMProviderSettings())

    assert isinstance(provider, MockLLMProvider)


def test_settings_from_env(monkeypatch) -> None:
    monkeypatch.setenv("ARVIS_LLM_PROVIDER", "mock")
    monkeypatch.setenv("ARVIS_LLM_MODEL", "test-model")

    settings = LLMProviderSettings.from_env()

    assert settings.provider == "mock"
    assert settings.model == "test-model"


def test_resolve_provider_from_explicit_settings() -> None:
    provider = resolve_provider(
        LLMProviderSettings(
            provider="mock",
            model="ignored-for-mock",
        )
    )

    assert isinstance(provider, MockLLMProvider)
