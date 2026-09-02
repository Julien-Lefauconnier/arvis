# arvis/kernel_core/process/process_interrupt_state.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProcessInterruptState:
    """Per-process interrupt-state slice.

    Deliberately empty since DM-H4 (campaign HARDEN, 2026-09-02): its
    only field was ``subscribed_interrupts``, the process-side half of
    a pub/sub nothing ever called (no reader, no writer besides the
    constructor default). The slice stays as process structure so a
    real interrupt state has its place when a design act adds one.
    """
