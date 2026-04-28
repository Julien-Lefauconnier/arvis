# arvis/adapters/llm/providers/registry.py

from __future__ import annotations

from arvis.adapters.llm.providers.base import BaseLLMProvider


def build_provider(
    name: str,
    *,
    model: str | None = None,
) -> BaseLLMProvider:
    normalized = name.strip().lower()

    if normalized == "openai":
        from arvis.adapters.llm.providers.openai import OpenAIAdapter

        return OpenAIAdapter(model=model or "gpt-4o-mini")

    if normalized == "anthropic":
        from arvis.adapters.llm.providers.anthropic import AnthropicProvider

        return AnthropicProvider(model=model or "claude-3-5-sonnet-latest")

    if normalized == "ollama":
        from arvis.adapters.llm.providers.ollama import OllamaProvider

        return OllamaProvider(model=model or "llama3.1")

    if normalized == "mock":
        from arvis.adapters.llm.providers.mock import MockLLMProvider

        return MockLLMProvider()

    raise ValueError(f"Unknown LLM provider: {name}")
