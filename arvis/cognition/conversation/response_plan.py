# arvis/cognition/conversation/response_plan.py

from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from .response_strategy_type import ResponseStrategyType
from .response_realization_mode import ResponseRealizationMode


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

    template_key: Optional[str] = None

    short_circuit: bool = False

    context_hints: Dict[str, Any] = field(default_factory=dict)

    # --------------------------------------------
    # LINGUISTIC LAYER (optional, non-executable)
    # --------------------------------------------
    generation_frame: Optional[Dict[str, Any]] = None
    prompt: Optional[str] = None