# arvis/kernel_core/interrupts/interrupt.py

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any

from arvis.kernel_core.interrupts.interrupt_type import CognitiveInterruptType


@dataclass
class CognitiveInterrupt:
    type: CognitiveInterruptType
    payload: Any | None = None
    target_process_id: str | None = None

    created_at: float = field(default_factory=time)
    metadata: dict[str, Any] = field(default_factory=dict)
