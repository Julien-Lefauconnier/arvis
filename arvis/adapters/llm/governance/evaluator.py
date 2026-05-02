# arvis/adapters/llm/governance/evaluator.py

from __future__ import annotations

from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.governance.decision import LLMGovernanceDecision
from arvis.adapters.llm.governance.policy import LLMGovernancePolicy


class LLMGovernanceEvaluator:
    @staticmethod
    def evaluate(
        request: LLMRequest,
        policy: LLMGovernancePolicy | None,
    ) -> LLMGovernanceDecision:
        if policy is None:
            return LLMGovernanceDecision.deny("missing_llm_governance_policy")

        if not policy.allow_llm:
            return LLMGovernanceDecision.deny("llm_execution_disabled")

        prompt = request.prompt or ""

        if len(prompt) > policy.max_prompt_chars:
            return LLMGovernanceDecision.deny("prompt_too_large")

        has_system = any(m.role == "system" for m in request.messages or [])

        if policy.require_system_prompt and not has_system:
            return LLMGovernanceDecision.deny("missing_system_prompt")

        if (
            request.max_tokens is not None
            and policy.max_output_tokens is not None
            and request.max_tokens > policy.max_output_tokens
        ):
            return LLMGovernanceDecision.deny("max_tokens_exceeds_policy")

        if (
            request.model is not None
            and policy.allowed_models
            and request.model not in policy.allowed_models
        ):
            return LLMGovernanceDecision.deny("model_not_allowed")

        all_text = " ".join(m.content for m in (request.messages or []))
        lowered = all_text.lower()

        for term in policy.blocked_terms:
            if term.lower() in lowered:
                return LLMGovernanceDecision.deny("blocked_term_detected")

        return LLMGovernanceDecision(
            allowed=True,
            reason="allowed",
            requires_audit=policy.audit_required,
        )
