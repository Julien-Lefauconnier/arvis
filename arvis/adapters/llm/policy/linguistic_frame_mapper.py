# arvis/adapters/llm/policy/linguistic_frame_mapper.py

from __future__ import annotations

from arvis.adapters.llm.contracts.context import ARVISContext
from arvis.adapters.llm.policy.behavior_policy import LLMBehaviorPolicy
from arvis.linguistic.acts.act_types import LinguisticActType
from arvis.linguistic.generation.generation_frame import LinguisticGenerationFrame


class LLMLinguisticFrameMapper:
    @staticmethod
    def from_context(ctx: ARVISContext) -> LinguisticGenerationFrame:
        """
        ARVIS → linguistic rendering mapping
        """

        risk = ctx.risk_score
        uncertainty = ctx.uncertainty_score

        # 🔴 High risk → abstention mode
        if risk >= 0.8:
            return LinguisticGenerationFrame(
                act=LinguisticActType.ABSTENTION,
                tone="neutral",
                verbosity="low",
                allow_speculation=False,
                allowed_entries=[],
                constraints=[
                    "Avoid speculation.",
                    "Abstain if the available context is insufficient.",
                ],
            )

        # 🟡 High uncertainty → cautious analytical
        if uncertainty >= 0.7:
            return LinguisticGenerationFrame(
                act=LinguisticActType.INFORMATION,
                tone="cautious",
                verbosity="medium",
                allow_speculation=False,
                allowed_entries=[],
                constraints=[
                    "Avoid speculation.",
                    "Abstain if the available context is insufficient.",
                ],
            )

        # 🟢 Stable
        return LinguisticGenerationFrame(
            act=LinguisticActType.INFORMATION,
            tone="neutral",
            verbosity="medium",
            allow_speculation=False,
            allowed_entries=[],
            constraints=[],
        )

    @staticmethod
    def from_behavior_policy(policy: LLMBehaviorPolicy) -> LinguisticGenerationFrame:
        return LinguisticGenerationFrame(
            act=policy.act,
            allowed_entries=[],
            tone=policy.tone,
            verbosity=policy.verbosity,
            allow_speculation=policy.allow_speculation,
            constraints=list(policy.constraints),
            preferences={
                "require_conservatism": policy.require_conservatism,
                "require_grounding": policy.require_grounding,
                "allow_abstention": policy.allow_abstention,
                "audit_required": policy.audit_required,
            },
        )
