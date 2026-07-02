# tests/api/test_llm_end_to_end.py
"""Governed LLM path: wiring + end-to-end invocation.

Verifies that a configured LLM adapter is injected into the kernel service
registry and is actually invoked through the full pipeline (the intent stage
enriches a non-ABSTAIN turn via the ``llm.generate`` syscall).
"""

from arvis.adapters.llm.contracts.execution_result import (
    LLMExecutionResult,
    LLMExecutionStatus,
)
from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.api.os import CognitiveOS, CognitiveOSConfig
from arvis.api.runtime.cognitive_runtime import CognitiveRuntime
from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline


class SpyLLMAdapter:
    """Records invocations and returns a valid governed execution result."""

    def __init__(self) -> None:
        self.calls = 0

    def generate(
        self,
        request: LLMRequest,
        *,
        preferred_provider: str | None = None,
    ) -> LLMExecutionResult:
        self.calls += 1
        return LLMExecutionResult(
            status=LLMExecutionStatus.SUCCESS,
            response=LLMResponse(content="hello"),
            retry_count=0,
            fallback_used=False,
            provider_attempts=(),
            evaluation={},
            observation={},
            error=None,
            degraded=False,
            replay_safe=True,
            require_confirmation=False,
        )


def test_llm_adapter_is_wired_into_service_registry() -> None:
    spy = SpyLLMAdapter()
    runtime = CognitiveRuntime(CognitivePipeline(), adapters={"llm": spy})
    assert runtime.services.llm_adapter is spy


def test_llm_adapter_invoked_end_to_end() -> None:
    spy = SpyLLMAdapter()
    os = CognitiveOS(config=CognitiveOSConfig(adapter_registry={"llm": spy}))

    # A low-risk turn is ALLOWed, so the intent stage enriches it through the
    # llm.generate syscall, exercising the full wiring end to end.
    os.run(user_id="u", cognitive_input={"risk": 0.1})

    assert spy.calls >= 1
