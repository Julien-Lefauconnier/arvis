# arvis/adapters/llm/runtime/executor.py

from __future__ import annotations

from collections.abc import Sequence

from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.observability.observer import LLMObserver
from arvis.adapters.llm.providers.base import BaseLLMProvider
from arvis.adapters.llm.runtime.evaluator import LLMResponseEvaluator
from arvis.adapters.llm.runtime.fallback_executor import FallbackExecutor
from arvis.adapters.llm.runtime.router import LLMRouter, LLMRoutingRequest
from arvis.errors.llm_runtime import (
    LLMExecutionContractViolation,
)


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
        self._observer = LLMObserver()
        self._evaluator = LLMResponseEvaluator()

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

            response = result.response

            if response is None:
                raise LLMExecutionContractViolation("fallback_executor_returned_none")

            obs = self._observer.observe(response)
            decision = self._evaluator.evaluate(obs)

            # NOTE: fallback path has no single provider for retry

            # Retry logic → re-run fallback executor
            if decision.retry:
                result = FallbackExecutor(
                    providers=self._fallback_providers,
                ).execute(request)
                response = result.response
                if response is None:
                    raise LLMExecutionContractViolation(
                        "fallback_executor_returned_none"
                    )
                obs = self._observer.observe(response)

            # Fallback logic
            elif decision.fallback and self._fallback_providers:
                result = FallbackExecutor(
                    providers=self._fallback_providers,
                ).execute(request)
                response = result.response
                if response is None:
                    raise LLMExecutionContractViolation(
                        "fallback_executor_returned_none"
                    )
                obs = self._observer.observe(response)

            # Inject metadata
            if obs is not None:
                response.metadata.setdefault("llm_observation", obs.to_dict())

            response.metadata["llm_evaluation"] = {
                "accept": decision.accept,
                "retry": decision.retry,
                "fallback": bool(decision.fallback),
                "require_confirmation": decision.require_confirmation,
            }

            response.metadata["execution_result"] = {
                "status": "success",
                "retry_count": 1 if decision.retry else 0,
                "fallback_used": bool(decision.fallback),
                "provider_attempts": [],
                "require_confirmation": decision.require_confirmation,
                "error": None,
                "degraded": False,
                "replay_safe": False,
            }

            return response

        provider = self._router.route(
            LLMRoutingRequest(
                preferred_provider=preferred_provider,
            )
        )

        response = provider.generate(request)

        obs = self._observer.observe(response)
        decision = self._evaluator.evaluate(obs)

        # Retry logic
        if decision.retry:
            response = provider.generate(request)
            obs = self._observer.observe(response)

        # Fallback logic
        elif decision.fallback and self._fallback_providers:
            result = FallbackExecutor(
                providers=self._fallback_providers,
            ).execute(request)
            response = result.response
            obs = self._observer.observe(response)

        # Inject observation
        if obs is not None:
            response.metadata.setdefault("llm_observation", obs.to_dict())

        # Inject evaluation
        response.metadata["llm_evaluation"] = {
            "accept": decision.accept,
            "retry": decision.retry,
            "fallback": decision.fallback,
            "require_confirmation": decision.require_confirmation,
        }

        response.metadata["execution_result"] = {
            "status": "success",
            "retry_count": 1 if decision.retry else 0,
            "fallback_used": bool(decision.fallback),
            "provider_attempts": [],
            "require_confirmation": decision.require_confirmation,
            "error": None,
            "degraded": False,
            "replay_safe": False,
        }

        return response
