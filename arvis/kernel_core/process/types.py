# arvis/kernel_core/process/types.py

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class CognitiveProcessId:
    value: str


class CognitiveProcessStatus(str, Enum):
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    WAITING_CONFIRMATION = "waiting_confirmation"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    ABORTED = "aborted"


class CognitiveProcessKind(str, Enum):
    USER_REQUEST = "user_request"
    MEMORY_CONSOLIDATION = "memory_consolidation"
    CONFLICT_RESOLUTION = "conflict_resolution"
    EXPLANATION = "explanation"
    COUNTERFACTUAL = "counterfactual"
    GOVERNANCE_REVIEW = "governance_review"
    REFLEXIVE_INTROSPECTION = "reflexive_introspection"
    SYSTEM_MAINTENANCE = "system_maintenance"
