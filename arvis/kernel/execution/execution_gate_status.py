# arvis/kernel/execution/execution_gate_status.py

from enum import Enum


class ExecutionGateStatus(str, Enum):
    READY = "ready"
    BLOCKED_CONFIRMATION = "blocked_confirmation"
    BLOCKED_ABSTAIN = "blocked_abstain"