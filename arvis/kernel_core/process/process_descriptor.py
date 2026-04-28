# arvis/kernel_core/process/process_descriptor.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from arvis.kernel_core.process.budget import CognitiveBudget
from arvis.kernel_core.process.priority import CognitivePriority
from arvis.kernel_core.process.types import (
    CognitiveProcessId,
    CognitiveProcessKind,
)


@dataclass(frozen=True)
class ProcessDescriptor:
    process_id: CognitiveProcessId
    kind: CognitiveProcessKind
    priority: CognitivePriority
    budget: CognitiveBudget
    created_tick: int
    user_id: str | None = None
    parent_process_id: CognitiveProcessId | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
