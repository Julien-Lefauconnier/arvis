# arvis/cognition/conversation/response_plan.py

from dataclasses import dataclass, field
from typing import Any

from .response_realization_mode import ResponseRealizationMode
from .response_strategy_type import ResponseStrategyType


@dataclass(frozen=True)
class ResponsePlan:
    """
    Declarative response plan.

    Kernel invariants:
    - immutable
    - no execution
    """

    strategy: ResponseStrategyType
    realization_mode: ResponseRealizationMode

    # simplified act type
    act_type: str

    template_key: str | None = None

    short_circuit: bool = False

    context_hints: dict[str, Any] = field(default_factory=dict)

    # --------------------------------------------
    # LINGUISTIC LAYER (optional, non-executable)
    # --------------------------------------------
    generation_frame: dict[str, Any] | None = None
    prompt: str | None = None
