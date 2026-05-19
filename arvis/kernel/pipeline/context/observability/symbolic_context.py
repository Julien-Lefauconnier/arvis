# arvis/kernel/pipeline/context/observability/symbolic_context.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ObservabilitySymbolicContext:
    symbolic_drift: Any | None = None
    symbolic_features: Any | None = None
