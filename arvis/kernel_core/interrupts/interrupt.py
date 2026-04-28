# arvis/kernel_core/interrupts/interrupt.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from time import time

from arvis.kernel_core.interrupts.interrupt_type import CognitiveInterruptType


@dataclass
class CognitiveInterrupt:
    type: CognitiveInterruptType
    payload: Optional[Any] = None
    target_process_id: Optional[str] = None

    created_at: float = field(default_factory=time)
    metadata: dict[str, Any] = field(default_factory=dict)
