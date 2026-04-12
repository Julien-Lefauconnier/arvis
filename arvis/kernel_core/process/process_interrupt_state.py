# arvis/kernel_core/process/process_interrupt_state.py

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProcessInterruptState:
    subscribed_interrupts: set[str] = field(default_factory=set)