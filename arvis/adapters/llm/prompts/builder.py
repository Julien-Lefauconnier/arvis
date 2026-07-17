# arvis/adapters/llm/prompts/builder.py

from __future__ import annotations

from dataclasses import fields, is_dataclass
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


# Wall-clock fields excluded from the prompt rendering: a repr embedding
# them makes the prompt, hence the LLM call and its pre-effect
# engagement digest, non-deterministic across identical runs.
_VOLATILE_INTENT_FIELDS = frozenset({"decided_at", "created_at", "timestamp"})


def _render_intent(intent: Any) -> str:
    """Deterministic rendering of the intent for the prompt.

    Explicit dataclass fields, volatile wall-clock fields excluded. The
    prompt content is part of what the run engages (P0-3-a6): it must
    be a deterministic function of the run, never of the clock.
    """
    if is_dataclass(intent) and not isinstance(intent, type):
        pairs = [
            f"{f.name}={getattr(intent, f.name, None)!r}"
            for f in fields(intent)
            if f.name not in _VOLATILE_INTENT_FIELDS
        ]
        return f"{type(intent).__qualname__}({', '.join(pairs)})"
    return str(intent)


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

{INTENT_ENRICHMENT_USER_TEMPLATE.format(intent=_render_intent(intent))}
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
