# arvis/adapters/llm/runtime/executor.py

from __future__ import annotations

from collections.abc import Sequence

from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.providers.base import BaseLLMProvider
from arvis.adapters.llm.runtime.fallback_executor import FallbackExecutor
from arvis.adapters.llm.runtime.router import LLMRouter, LLMRoutingRequest


class LLMRuntimeExecutor:
    """
    Runtime executor for LLM requests.

    Responsibilities:
    - execute explicit fallback providers when provided
    - otherwise resolve one provider through the router
    - return a normalized LLMResponse
    """

    def __init__(
        self,
        router: LLMRouter | None = None,
        fallback_providers: Sequence[BaseLLMProvider] | None = None,
    ) -> None:
        self._router = router or LLMRouter()
        self._fallback_providers = fallback_providers

    def execute(
        self,
        request: LLMRequest,
        *,
        preferred_provider: str | None = None,
    ) -> LLMResponse:
        if self._fallback_providers is not None:
            result = FallbackExecutor(
                providers=self._fallback_providers,
            ).execute(request)

            return result.response

        provider = self._router.route(
            LLMRoutingRequest(
                preferred_provider=preferred_provider,
            )
        )

        return provider.generate(request)
