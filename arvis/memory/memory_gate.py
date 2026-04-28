# arvis/memory/memory_gate.py

from arvis.memory.memory_intent import MemoryIntent


class MemoryGate:
    def allow(self, intent: MemoryIntent) -> bool:
        return intent is MemoryIntent.CONFIRMED
