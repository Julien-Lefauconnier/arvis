# arvis/cognition/conversation/response_strategy_decision.py

from dataclasses import dataclass, field
from typing import Any

from .response_strategy_type import ResponseStrategyType


@dataclass(frozen=True)
class ResponseStrategyDecision:
    """
    Declarative decision describing the response strategy.

    Kernel invariants:
    - immutable
    - no execution
    - fully traceable
    """

    strategy: ResponseStrategyType
    reason: str

    confidence: float = 1.0
    signals: dict[str, Any] = field(default_factory=dict)
