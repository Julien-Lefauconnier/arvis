# arvis/kernel/pipeline/services/llm_request_builder.py

from __future__ import annotations

from typing import Any, Protocol

from arvis.adapters.llm.context.arvis_context_mapper import ARVISContextMapper
from arvis.adapters.llm.contracts.options import LLMOptions
from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.policy.behavior_policy_mapper import (
    LLMBehaviorPolicyMapper,
)
from arvis.adapters.llm.policy.linguistic_frame_mapper import (
    LLMLinguisticFrameMapper,
)
from arvis.adapters.llm.prompts.builder import PromptBuilder
from arvis.adapters.llm.prompts.prompt_to_messages import PromptToMessagesMapper


class CognitiveStateLike(Protocol):
    regime: Any
    uncertainty: Any
    risk: Any


class PipelineContextLike(Protocol):
    extra: dict[str, Any]
    cognitive_state: CognitiveStateLike | None


class LLMRequestBuilder:
    @staticmethod
    def build_intent_enrichment_request(
        ctx: PipelineContextLike,
        intent: Any,
    ) -> LLMRequest:
        arvis_ctx = ARVISContextMapper.from_pipeline_ctx(ctx)

        # 1. Policy (what to do)
        policy = LLMBehaviorPolicyMapper.from_arvis_context(arvis_ctx)

        # 2. Linguistic frame (how to speak)
        frame = LLMLinguisticFrameMapper.from_behavior_policy(policy)

        # 3. Prompt contract
        prompt_contract = PromptBuilder.build_intent_enrichment_prompt(
            intent,
            context=arvis_ctx,
            policy=policy,
            frame=frame,
        )

        # 4. Build request
        return LLMRequest(
            messages=PromptToMessagesMapper.to_messages(prompt_contract),
            options=LLMOptions(
                temperature=policy.temperature, max_tokens=policy.max_output_tokens
            ),
            tags=[
                f"linguistic_act:{frame.act.value}",
            ],
        )
