# arvis/adapters/llm/llm_executor.py

from __future__ import annotations

from typing import Any

from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.governance.policy import LLMGovernancePolicy
from arvis.adapters.registry import get_llm_adapter
from arvis.conversation.response_plan import ResponsePlan
from arvis.conversation.response_realization_mode import ResponseRealizationMode
from arvis.linguistic.acts.act_types import LinguisticActType
from arvis.linguistic.acts.linguistic_act import LinguisticAct
from arvis.linguistic.realization.realization_service import (
    LinguisticRealizationService,
)


class LLMExecutor:
    """
    Final execution layer.
    """

    @staticmethod
    def execute(plan: ResponsePlan, ctx: Any | None = None) -> str:
        # TEMPLATE PATH
        if plan.realization_mode == ResponseRealizationMode.TEMPLATE:
            act = LinguisticAct(LinguisticActType(plan.act_type))
            return LinguisticRealizationService.realize(act)

        # LLM PATH
        if plan.realization_mode == ResponseRealizationMode.LLM:
            adapter = get_llm_adapter(ctx)

            if adapter is None:
                raise RuntimeError("No LLM adapter configured.")

            if not plan.prompt:
                raise RuntimeError("Missing prompt for LLM execution.")

            policy = None
            if ctx is not None:
                extra = getattr(ctx, "extra", {})
                raw_policy = extra.get("llm_policy")
                if isinstance(raw_policy, LLMGovernancePolicy):
                    policy = raw_policy

            request = LLMRequest(
                prompt=plan.prompt,
                metadata={"source": "response_plan"},
            )

            if policy is None:
                raise RuntimeError("Missing LLM governance policy.")

            response = adapter.generate(
                request,
            )

            content = getattr(response, "content", None)

            if not isinstance(content, str):
                raise RuntimeError("Invalid LLM response format.")

            return content

        raise RuntimeError("Unsupported realization mode.")
