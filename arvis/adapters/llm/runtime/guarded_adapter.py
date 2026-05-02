# arvis/adapters/llm/runtime/guarded_adapter.py

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from arvis.adapters.llm.contracts.errors import LLMPolicyViolation
from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.governance.budget import LLMBudget
from arvis.adapters.llm.governance.evaluator import LLMGovernanceEvaluator
from arvis.adapters.llm.governance.policy import LLMGovernancePolicy
from arvis.adapters.llm.governance.risk import LLMRisk, LLMRiskLevel
from arvis.adapters.llm.runtime.executor import LLMRuntimeExecutor


@dataclass(frozen=True, slots=True)
class GuardedLLMAdapter:
    executor: LLMRuntimeExecutor = field(default_factory=LLMRuntimeExecutor)
    policy: LLMGovernancePolicy = field(
        default_factory=LLMGovernancePolicy.permissive_for_dev
    )

    budget: LLMBudget | None = None
    max_risk: LLMRiskLevel = LLMRiskLevel.HIGH
    risk_evaluator: Callable[[LLMRequest], LLMRisk] = field(
        default_factory=lambda: GuardedLLMAdapter._default_risk_evaluator
    )

    def generate(
        self,
        request: LLMRequest,
        *,
        preferred_provider: str | None = None,
    ) -> LLMResponse:
        # --------------------------------------------------
        # 1. POLICY
        # --------------------------------------------------
        decision = LLMGovernanceEvaluator.evaluate(
            request=request,
            policy=self.policy,
        )

        if not decision.allowed:
            raise LLMPolicyViolation(decision.reason)

        # --------------------------------------------------
        # 2. RISK (simple baseline for now)
        # --------------------------------------------------
        risk = self.risk_evaluator(request)

        if not risk.is_allowed(self.max_risk):
            raise LLMPolicyViolation(
                f"LLM risk too high: {risk.level} > {self.max_risk}"
            )

        # --------------------------------------------------
        # 3. EXECUTION
        # --------------------------------------------------
        response = self.executor.execute(
            request,
            preferred_provider=preferred_provider,
        )

        # --------------------------------------------------
        # 4. BUDGET CHECK (post-call)
        # --------------------------------------------------
        if self.budget is not None and response.usage is not None:
            if not self.budget.is_within(
                tokens=response.usage.total_tokens,
                cost=response.usage.cost,
            ):
                raise LLMPolicyViolation("LLM budget exceeded")

        # --------------------------------------------------
        # 5. METADATA ENRICHMENT
        # --------------------------------------------------
        metadata: dict[str, Any] = dict(response.metadata or {})

        metadata["llm"] = {
            "provider": response.provider,
            "model": response.model,
        }

        metadata["llm_governance"] = {
            "allowed": decision.allowed,
            "reason": decision.reason,
            "requires_audit": decision.requires_audit,
            "risk": risk.level.value,
        }

        if response.usage is not None:
            metadata["llm_usage"] = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
                "cost": response.usage.cost,
                "latency_ms": response.usage.latency_ms,
            }

        # --------------------------------------------------
        # 6. FINAL RESPONSE
        # --------------------------------------------------
        return LLMResponse(
            content=response.content,
            usage=response.usage,
            provider=response.provider,
            model=response.model,
            finish_reason=response.finish_reason,
            trace_id=response.trace_id,
            metadata=metadata,
        )

    # --------------------------------------------------
    # INTERNALS
    # --------------------------------------------------

    @staticmethod
    def _default_risk_evaluator(request: LLMRequest) -> LLMRisk:
        """
        Minimal baseline risk evaluation.

        Will be replaced later by:
        - prompt analysis
        - intent classification
        - content sensitivity detection
        """
        # TODO: plug real risk evaluator
        return LLMRisk(LLMRiskLevel.LOW)
