# arvis/kernel_core/interrupts/interrupt_bus.py

from __future__ import annotations

from collections import deque

from arvis.kernel_core.interrupts.interrupt import CognitiveInterrupt


class CognitiveInterruptBus:
    """Kernel-level interrupt queue with explicit-target routing.

    Responsibilities:
    - queue interrupts (``emit``)
    - hand the drained batch to the scheduler (``drain``)
    - name the processes an interrupt wakes (``match``)

    DM-H4 (campaign HARDEN, audit P1-15b, 2026-09-02): the bus used to
    carry a subscribe/unsubscribe half and a per-type subscriber table
    that nothing in the runtime ever called; ``match`` could only ever
    route by ``target_process_id`` in practice. The dead half is
    removed rather than left to document a pub/sub that does not
    exist; reintroducing one is a deliberate future design act.
    """

    def __init__(self) -> None:
        self._queue: deque[CognitiveInterrupt] = deque()

    def emit(self, interrupt: CognitiveInterrupt) -> None:
        self._queue.append(interrupt)

    def drain(self) -> list[CognitiveInterrupt]:
        events = list(self._queue)
        self._queue.clear()
        return events

    def match(self, interrupt: CognitiveInterrupt) -> list[str]:
        """Process ids to wake: the explicit target, or nobody."""
        if interrupt.target_process_id:
            return [interrupt.target_process_id]
        return []
