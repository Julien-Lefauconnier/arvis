# arvis/kernel_core/interrupts/interrupt_type.py

from __future__ import annotations

from enum import StrEnum


class CognitiveInterruptType(StrEnum):
    USER_INPUT = "user_input"
    TOOL_RESULT = "tool_result"
    MEMORY_READY = "memory_ready"
    CONFIRMATION_RECEIVED = "confirmation_received"
    TIMEOUT = "timeout"
    INTERNAL_SIGNAL = "internal_signal"
    EXTERNAL_EVENT = "external_event"
    SYSTEM_SIGNAL = "system_signal"
