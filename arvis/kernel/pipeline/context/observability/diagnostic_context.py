# arvis/kernel/pipeline/context/observability/diagnostic_context.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ObservabilityDiagnosticContext:
    system_tension: Any | None = None
    degraded_components: list[str] = field(default_factory=list)

    warnings: list[str] = field(default_factory=list)

    metrics: dict[str, Any] = field(default_factory=dict)
