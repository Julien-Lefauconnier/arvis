# arvis/kernel/execution/execution_gate_status.py

from enum import StrEnum


class ExecutionGateStatus(StrEnum):
    READY = "ready"
    BLOCKED_CONFIRMATION = "blocked_confirmation"
    BLOCKED_ABSTAIN = "blocked_abstain"
