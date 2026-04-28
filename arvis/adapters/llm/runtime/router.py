# arvis/adapters/llm/runtime/router.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.adapters.llm.providers.base import BaseLLMProvider
from arvis.adapters.llm.providers.resolver import (
    LLMProviderSettings,
    resolve_provider,
)


@dataclass(frozen=True, slots=True)
class LLMRoutingRequest:
    use_case: str = "default"
    latency_sensitive: bool = False
    cost_sensitive: bool = False
    offline_required: bool = False
    preferred_provider: str | None = None
    preferred_model: str | None = None


class LLMRouter:
    def route(self, request: LLMRoutingRequest | None = None) -> BaseLLMProvider:
        routing_request = request or LLMRoutingRequest()

        settings = self._build_settings(routing_request)
        return resolve_provider(settings)

    def _build_settings(
        self,
        request: LLMRoutingRequest,
    ) -> LLMProviderSettings:
        provider = self._select_provider_name(request)

        return LLMProviderSettings(
            provider=provider,
            model=request.preferred_model,
        )

    def _select_provider_name(self, request: LLMRoutingRequest) -> str:
        if request.preferred_provider:
            return request.preferred_provider

        if request.offline_required:
            return "ollama"

        if request.cost_sensitive:
            return "ollama"

        if request.latency_sensitive:
            return "openai"

        return "mock"
