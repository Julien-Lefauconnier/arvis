# arvis/adapters/llm/prompts/builder.py

from __future__ import annotations

from typing import Any

from arvis.adapters.llm.contracts.context import ARVISContext
from arvis.adapters.llm.policy.behavior_policy import LLMBehaviorPolicy
from arvis.adapters.llm.prompts.contract import PromptContract, PromptPurpose
from arvis.adapters.llm.prompts.sanitizer import PromptSanitizer
from arvis.adapters.llm.prompts.templates import (
    INTENT_ENRICHMENT_SYSTEM_PROMPT,
    INTENT_ENRICHMENT_USER_TEMPLATE,
)
from arvis.linguistic.generation.generation_frame import LinguisticGenerationFrame


def _build_arvis_context_block(ctx: ARVISContext | None) -> str:
    if ctx is None:
        return ""

    parts = ["[ARVIS CONTEXT]"]
    parts.append(f"- Risk score: {ctx.risk_score:.2f}")
    parts.append(f"- Uncertainty score: {ctx.uncertainty_score:.2f}")
    parts.append(f"- Stability score: {ctx.stability_score:.2f}")
    parts.append(f"- Confidence score: {ctx.confidence_score:.2f}")

    if ctx.constraints:
        parts.append("\n[CONSTRAINTS]")
        parts.extend(f"- {item}" for item in ctx.constraints)

    if ctx.objectives:
        parts.append("\n[OBJECTIVES]")
        parts.extend(f"- {item}" for item in ctx.objectives)

    return "\n".join(parts)


def _build_linguistic_frame_block(frame: LinguisticGenerationFrame | None) -> str:
    if frame is None:
        return ""

    parts = ["[LINGUISTIC FRAME]"]
    parts.append(f"- Act: {frame.act.value}")
    parts.append(f"- Tone: {frame.tone}")
    parts.append(f"- Verbosity: {frame.verbosity}")
    parts.append(f"- Allow speculation: {frame.allow_speculation}")

    if frame.constraints:
        parts.append("\n[LINGUISTIC CONSTRAINTS]")
        parts.extend(f"- {item}" for item in frame.constraints)

    return "\n".join(parts)


class PromptBuilder:
    @staticmethod
    def build_intent_enrichment_prompt(
        intent: Any,
        context: ARVISContext | None = None,
        policy: LLMBehaviorPolicy | None = None,
        frame: LinguisticGenerationFrame | None = None,
    ) -> PromptContract:
        context_block = _build_arvis_context_block(context)
        frame_block = _build_linguistic_frame_block(frame)

        user = f"""
{context_block}

{frame_block}

{INTENT_ENRICHMENT_USER_TEMPLATE.format(intent=str(intent))}
"""

        constraints = [
            "Do not invent missing runtime state.",
            "Do not expose hidden chain-of-thought.",
            "Return only operationally useful information.",
        ]

        if policy is not None and getattr(policy, "constraints", None):
            constraints.extend(policy.constraints)

        if frame is not None and frame.constraints:
            constraints.extend(frame.constraints)

        return PromptContract(
            purpose=PromptPurpose.INTENT_ENRICHMENT,
            system=PromptSanitizer.sanitize(INTENT_ENRICHMENT_SYSTEM_PROMPT),
            user=PromptSanitizer.sanitize(user),
            constraints=list(dict.fromkeys(constraints)),
            metadata={
                "source": "IntentStage",
                "linguistic_act": frame.act.value if frame else "information",
            },
        )
