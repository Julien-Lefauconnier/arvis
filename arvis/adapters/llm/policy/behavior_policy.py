# arvis/adapters/llm/policy/behavior_policy.py

from __future__ import annotations

from dataclasses import dataclass, field

from arvis.linguistic.acts.act_types import LinguisticActType


@dataclass(frozen=True, slots=True)
class LLMBehaviorPolicy:
    allow_speculation: bool
    require_conservatism: bool
    require_grounding: bool
    allow_abstention: bool
    audit_required: bool

    act: LinguisticActType
    tone: str
    verbosity: str

    max_output_tokens: int
    temperature: float

    constraints: tuple[str, ...] = field(default_factory=tuple)

    @staticmethod
    def safe_default() -> LLMBehaviorPolicy:
        return LLMBehaviorPolicy(
            allow_speculation=False,
            require_conservatism=True,
            require_grounding=True,
            allow_abstention=True,
            audit_required=True,
            act=LinguisticActType.INFORMATION,
            tone="neutral",
            verbosity="minimal",
            max_output_tokens=512,
            temperature=0.2,
            constraints=(
                "Do not invent missing runtime state.",
                "Do not expose hidden chain-of-thought.",
                "Prefer abstention over unsupported claims.",
            ),
        )
