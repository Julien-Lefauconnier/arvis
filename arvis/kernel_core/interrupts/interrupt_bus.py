# arvis/kernel_core/interrupts/interrupt_bus.py

from __future__ import annotations

from collections import defaultdict, deque

from arvis.kernel_core.interrupts.interrupt import CognitiveInterrupt
from arvis.kernel_core.interrupts.interrupt_type import CognitiveInterruptType


class CognitiveInterruptBus:
    """
    Kernel-level interrupt dispatcher.

    Responsibilities:
    - queue interrupts
    - dispatch to subscribers
    """

    def __init__(self) -> None:
        self._queue: deque[CognitiveInterrupt] = deque()
        self._subscribers: dict[CognitiveInterruptType, list[str]] = defaultdict(list)

    def emit(self, interrupt: CognitiveInterrupt) -> None:
        self._queue.append(interrupt)

    def subscribe(
        self,
        process_id: str,
        interrupt_type: CognitiveInterruptType,
    ) -> None:
        if process_id not in self._subscribers[interrupt_type]:
            self._subscribers[interrupt_type].append(process_id)

    def unsubscribe(
        self,
        process_id: str,
        interrupt_type: CognitiveInterruptType,
    ) -> None:
        if process_id in self._subscribers[interrupt_type]:
            self._subscribers[interrupt_type].remove(process_id)

    def drain(self) -> list[CognitiveInterrupt]:
        events = list(self._queue)
        self._queue.clear()
        return events

    def match(self, interrupt: CognitiveInterrupt) -> list[str]:
        """
        Returns process_ids that should be woken up.
        """
        targets = set()

        if interrupt.target_process_id:
            targets.add(interrupt.target_process_id)

        targets.update(self._subscribers.get(interrupt.type, []))

        return list(targets)
