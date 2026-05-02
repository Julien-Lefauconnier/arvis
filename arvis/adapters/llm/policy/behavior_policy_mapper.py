# arvis/adapters/llm/policy/behavior_policy_mapper.py

from __future__ import annotations

from arvis.adapters.llm.contracts.context import ARVISContext
from arvis.adapters.llm.policy.behavior_policy import LLMBehaviorPolicy
from arvis.linguistic.acts.act_types import LinguisticActType


class LLMBehaviorPolicyMapper:
    @staticmethod
    def from_arvis_context(ctx: ARVISContext) -> LLMBehaviorPolicy:
        constraints: list[str] = [
            "Do not expose hidden chain-of-thought.",
            "Do not introduce actions not present in the validated intent.",
            "Do not override ARVIS gate, policy, or stability decisions.",
        ]

        require_conservatism = (
            ctx.risk_score >= 0.65
            or ctx.uncertainty_score >= 0.65
            or ctx.stability_score <= 0.35
            or ctx.confidence_score <= 0.45
        )

        allow_speculation = (
            ctx.risk_score < 0.35
            and ctx.uncertainty_score < 0.35
            and ctx.confidence_score >= 0.75
        )

        allow_abstention = (
            ctx.uncertainty_score >= 0.55
            or ctx.confidence_score <= 0.55
            or ctx.stability_score <= 0.45
        )

        require_grounding = (
            ctx.uncertainty_score >= 0.45
            or ctx.confidence_score <= 0.7
            or ctx.risk_score >= 0.45
        )

        if require_conservatism:
            constraints.extend(
                [
                    "Use conservative reasoning.",
                    "Avoid speculation.",
                    "State uncertainty explicitly when relevant.",
                    "Prefer safe, bounded, verifiable output.",
                ]
            )

        if require_grounding:
            constraints.append("Ground the response in provided context only.")

        if allow_abstention:
            constraints.append("Abstain if the available context is insufficient.")

        constraints.extend(ctx.constraints)

        if ctx.risk_score >= 0.8:
            constraints.extend(
                [
                    "Avoid speculation.",
                    "Abstain if the available context is insufficient.",
                ]
            )
            act = LinguisticActType.ABSTENTION
            tone = "cautious"
            verbosity = "minimal"
            temperature = 0.0
            max_output_tokens = 256

        elif ctx.uncertainty_score >= 0.7:
            act = LinguisticActType.INFORMATION
            tone = "careful"
            verbosity = "compact"
            temperature = 0.1
            max_output_tokens = 384

        elif ctx.stability_score <= 0.4:
            act = LinguisticActType.REQUEST_CONFIRMATION
            tone = "careful"
            verbosity = "minimal"
            temperature = 0.1
            max_output_tokens = 256

        else:
            act = LinguisticActType.INFORMATION
            tone = "neutral"
            verbosity = "structured"
            temperature = 0.2
            max_output_tokens = 512

        return LLMBehaviorPolicy(
            allow_speculation=allow_speculation,
            require_conservatism=require_conservatism,
            require_grounding=require_grounding,
            allow_abstention=allow_abstention,
            audit_required=True,
            act=act,
            tone=tone,
            verbosity=verbosity,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            constraints=tuple(dict.fromkeys(constraints)),
        )
