# arvis/adapters/llm/providers/resolver.py

from __future__ import annotations

import os
from dataclasses import dataclass

from arvis.adapters.llm.providers.base import BaseLLMProvider
from arvis.adapters.llm.providers.registry import build_provider


@dataclass(frozen=True, slots=True)
class LLMProviderSettings:
    provider: str = "mock"
    model: str | None = None

    @staticmethod
    def from_env() -> LLMProviderSettings:
        return LLMProviderSettings(
            provider=os.getenv("ARVIS_LLM_PROVIDER", "mock"),
            model=os.getenv("ARVIS_LLM_MODEL"),
        )


def resolve_provider(
    settings: LLMProviderSettings | None = None,
) -> BaseLLMProvider:
    active_settings = settings or LLMProviderSettings.from_env()

    return build_provider(
        active_settings.provider,
        model=active_settings.model,
    )
