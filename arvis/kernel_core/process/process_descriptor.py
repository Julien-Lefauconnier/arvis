# arvis/kernel_core/process/process_descriptor.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from arvis.kernel_core.process.types import (
    CognitiveProcessId,
    CognitiveProcessKind,
)
from arvis.kernel_core.process.priority import CognitivePriority
from arvis.kernel_core.process.budget import CognitiveBudget


@dataclass(frozen=True)
class ProcessDescriptor:
    process_id: CognitiveProcessId
    kind: CognitiveProcessKind
    priority: CognitivePriority
    budget: CognitiveBudget
    created_tick: int
    user_id: Optional[str] = None
    parent_process_id: Optional[CognitiveProcessId] = None
    metadata: dict[str, Any] = field(default_factory=dict)
