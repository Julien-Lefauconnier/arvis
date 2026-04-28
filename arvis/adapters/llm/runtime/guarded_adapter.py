# arvis/adapters/llm/runtime/guarded_adapter.py

from __future__ import annotations

from dataclasses import dataclass, field

from arvis.adapters.llm.contracts.errors import LLMPolicyViolation
from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.governance.evaluator import LLMGovernanceEvaluator
from arvis.adapters.llm.governance.policy import LLMGovernancePolicy
from arvis.adapters.llm.runtime.executor import LLMRuntimeExecutor


@dataclass(frozen=True, slots=True)
class GuardedLLMAdapter:
    executor: LLMRuntimeExecutor = field(default_factory=LLMRuntimeExecutor)
    policy: LLMGovernancePolicy = field(
        default_factory=LLMGovernancePolicy.permissive_for_dev
    )

    def generate(
        self,
        request: LLMRequest,
        *,
        preferred_provider: str | None = None,
    ) -> LLMResponse:
        decision = LLMGovernanceEvaluator.evaluate(
            request=request,
            policy=self.policy,
        )

        if not decision.allowed:
            raise LLMPolicyViolation(decision.reason)

        response = self.executor.execute(
            request,
            preferred_provider=preferred_provider,
        )

        metadata = dict(response.metadata)

        metadata["llm_governance"] = {
            "allowed": decision.allowed,
            "reason": decision.reason,
            "requires_audit": decision.requires_audit,
        }

        return LLMResponse(
            content=response.content,
            raw=response.raw,
            metadata=metadata,
        )