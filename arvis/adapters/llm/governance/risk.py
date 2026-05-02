# arvis/adapters/llm/governance/risk.py

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class LLMRiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(slots=True, frozen=True)
class LLMRisk:
    """
    Represents the evaluated risk of an LLM call.
    """

    level: LLMRiskLevel

    # Optional signals
    reason: str | None = None

    def is_high(self) -> bool:
        return self.level == LLMRiskLevel.HIGH

    def is_allowed(self, max_level: LLMRiskLevel) -> bool:
        order = {
            LLMRiskLevel.LOW: 0,
            LLMRiskLevel.MEDIUM: 1,
            LLMRiskLevel.HIGH: 2,
        }

        return order[self.level] <= order[max_level]
