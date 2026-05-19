# arvis/kernel/pipeline/context/observability/state_context.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from arvis.ir.state import CognitiveStateIR


@dataclass
class ObservabilityStateContext:
    ir_state: CognitiveStateIR | None = None
    cognitive_state: Any | None = None
