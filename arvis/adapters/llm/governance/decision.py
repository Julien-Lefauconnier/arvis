# arvis/adapters/llm/governance/decision.py

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class LLMGovernanceDecision:
    allowed: bool
    reason: str
    requires_audit: bool = True
    metadata: dict[str, str] = field(default_factory=dict)

    @staticmethod
    def deny(reason: str) -> LLMGovernanceDecision:
        return LLMGovernanceDecision(allowed=False, reason=reason)
