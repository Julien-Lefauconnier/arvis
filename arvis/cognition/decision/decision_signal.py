# arvis/cognition/decision/decision_signal.py

from dataclasses import dataclass, field
from typing import Any

from arvis.cognition.conflict.conflict_signal import ConflictSignal
from arvis.memory.memory_intent import MemoryIntent
from arvis.reasoning.reasoning_gap import ReasoningGap
from arvis.reasoning.reasoning_intent import ReasoningIntent
from arvis.uncertainty.uncertainty_frame import UncertaintyFrame


@dataclass(frozen=True)
class DecisionSignal:
    """
    Pure cognitive decision signal.

    Kernel invariants:
    - immutable
    - no execution
    - no backend dependency
    """

    memory_intent: MemoryIntent = MemoryIntent.NONE
    reason: str = ""

    gaps: list[ReasoningGap] = field(default_factory=list)
    reasoning_intents: list[ReasoningIntent] = field(default_factory=list)
    uncertainty_frames: list[UncertaintyFrame] = field(default_factory=list)
    conflicts: list[ConflictSignal] = field(default_factory=list)

    context_hints: dict[str, Any] = field(default_factory=dict)
    memory_influence: dict[str, Any] = field(default_factory=dict)
